#!/usr/bin/env python3
"""Generate composition data, direct MIDI, and optional dry sampled audio."""
import argparse,json,struct,subprocess,wave,math,shutil,tempfile,hashlib
from pathlib import Path
import numpy as np
import yaml
from jonathanmarmor import make_music

def generate(config, from_pulses=False):
    melodies={'original 6':[6,12,9,4,0,2], 'original 5':[6,12,9,4,0], 'another 5':[6,9,4,0,2]}
    melody=config['melody']
    if isinstance(melody,str): melody=melodies[melody]
    progress = config.get('inward_progress')
    if progress is not None:
        if len(progress) != config['steps'] + 1 or not math.isclose(progress[0],0) or not math.isclose(progress[-1],1):
            raise ValueError('inward_progress must have steps+1 values, starting at 0 and ending at 1')
        if not all(math.isfinite(x) for x in progress) or any(b <= a for a,b in zip(progress,progress[1:])):
            raise ValueError('inward_progress must be finite and strictly increasing')
    instruments=[]
    for i,part in enumerate(config['ensemble']):
        instruments.append(dict(short=str(i+1),start=part['start'],init_transposition=part['init_transposition'],interval=-part['init_transposition']/config['steps']))
    notes=make_music([x+config['target_transposition'] for x in melody],instruments,{i['start']:i for i in instruments},config['steps'],config.get('second_movement',True), config.get('progressive_final_contraction',False), progress)
    first_movement = None
    if from_pulses:
        if not config.get('second_movement', True):
            raise ValueError('--from-pulses requires second_movement: true')
        first_movement = make_music([x+config['target_transposition'] for x in melody], instruments, {i['start']:i for i in instruments}, config['steps'], False, inward_progress=progress)
    parts=[]
    for i,part in enumerate(config['ensemble']):
        assert -100<=part['pan']<=100 and 0<=part['midi_program']<=127
        parts.append(dict(part=i+1,name=part['name'],program=part['midi_program'],pan=part['pan'],notes=[[n.raw_pitches[0].ps,n.raw_duration] for n in (notes[str(i+1)][len(first_movement[str(i+1)]):] if from_pulses else notes[str(i+1)])]))
    return dict(bpm=config['tempo_bpm'],parts=parts)

def encode_pitch(pitch):
    """Return a nearest MIDI note and bend with a +/-2-semitone range."""
    if not math.isfinite(pitch) or not 0 <= pitch <= 127:
        raise ValueError(f'Pitch outside MIDI range: {pitch}')
    note = int(math.floor(pitch + 0.5))
    bend = round(8192 + (pitch - note) * 8192 / 2)
    return note, bend

def render(music,base,audio,soundfont):
    p=base.parent;bpm=music['bpm'];ppq=960;sr=44100
    temp_handle=tempfile.TemporaryDirectory(prefix="marmor-render-")
    tempdir=Path(temp_handle.name)
    def vlq(n):
        out=[n&127];n>>=7
        while n:out.insert(0,(n&127)|128);n>>=7
        return bytes(out)
    def track(events):
        prev=0;data=bytearray()
        for tick,msg in sorted(events,key=lambda x:x[0]):
            data+=vlq(tick-prev)+msg;prev=tick
        data+=b'\x00\xff\x2f\x00'
        return b'MTrk'+struct.pack('>I',len(data))+data
    def midi(tracks):return b'MThd'+struct.pack('>IHHH',6,1,len(tracks),ppq)+b''.join(tracks)
    tempo=track([(0,b'\xff\x51\x03'+round(60000000/bpm).to_bytes(3,'big'))])
    tracks=[tempo];beats=max(sum(n[1] for n in part['notes']) for part in music['parts']);frames=round((beats*60/bpm+3)*sr)
    mix=np.zeros((frames,2),np.float32) if audio else None;stats=[]
    for ch,part in enumerate(music['parts']):
        name=f"Part {ch+1} — {part['name']}".encode()
        pan=round(64+part['pan']*(.64 if part['pan']<0 else .63))
        ev=[(0,b'\xff\x03'+vlq(len(name))+name),(0,bytes([0xc0+ch,part['program']]))]
        for cc,val in [(10,pan),(7,100),(11,127),(91,0),(93,0)]:ev.append((0,bytes([0xb0+ch,cc,val])))
        microtonal = any(not math.isclose(pitch, round(pitch), abs_tol=1e-9, rel_tol=0)
                         for pitch, _ in part['notes'])
        if microtonal:
            # RPN 0 explicitly sets each voice's pitch-bend range to +/-2 semitones.
            for cc, val in [(101,0),(100,0),(6,2),(38,0),(101,127),(100,127)]:
                ev.append((0, bytes([0xb0+ch, cc, val])))
        beat=0
        for pitch,dur in part['notes']:
            assert math.isfinite(dur) and dur > 0
            note, bend = encode_pitch(pitch)
            tick = round(beat*ppq)
            if microtonal:
                ev.append((tick, bytes([0xe0+ch, bend & 127, bend >> 7])))
            ev.extend([(tick,bytes([0x90+ch,note,85])),(round((beat+.94*dur)*ppq),bytes([0x80+ch,note,0]))]);beat+=dur
        ev.append((round(beat*ppq),bytes([0xb0+ch,123,0])))
        tracks.append(track(ev))
        if audio:
            # Render centered, then collapse each instrument to mono so hard pans remain exact.
            centered=[(t,bytes([msg[0],10,64]) if len(msg)==3 and msg[0]==0xb0+ch and msg[1]==10 else msg) for t,msg in ev]
            stemmid=tempdir/f'part_{ch+1}.mid';stemwav=tempdir/f'part_{ch+1}.wav'
            stemmid.write_bytes(midi([tempo,track(centered)]))
            r=subprocess.run(['fluidsynth','-ni','-R','0','-C','0','-g','.5','-r',str(sr),'-F',str(stemwav),str(soundfont),str(stemmid)],capture_output=True,text=True)
            if r.returncode:raise RuntimeError(r.stderr)
            with wave.open(str(stemwav),'rb') as w:
                assert w.getframerate()==sr and w.getnchannels()==2 and w.getsampwidth()==2
                mono=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float32).mean(axis=1)/32768
            mono=mono[:frames];rms=float(np.sqrt(np.mean(mono**2)));gain=.055/rms
            angle=(part['pan']/100+1)*math.pi/4;left=math.cos(angle);right=math.sin(angle)
            if part['pan']==-100:right=0
            if part['pan']==100:left=0
            mix[:len(mono),0]+=mono*gain*left;mix[:len(mono),1]+=mono*gain*right
            stats.append(dict(part=ch+1,name=part['name'],pan=part['pan'],midi_pan=pan,input_rms=rms,gain=gain))
            print(f"Rendered {ch+1}: {part['name']}",flush=True)
            stemmid.unlink();stemwav.unlink()
    base.with_suffix('.mid').write_bytes(midi(tracks))
    temp_handle.cleanup()
    if not audio:
        return
    peak=float(abs(mix).max());mix*=.9/max(peak,.9)
    assert np.isfinite(mix).all() and abs(mix).max()<=.90001
    with wave.open(str(base.with_suffix('.wav')),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((mix*32767).astype('<i2').tobytes())
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(base.with_suffix('.wav')),'-c:a','libmp3lame','-b:a','256k',str(base.with_suffix('.mp3'))],check=True)
    report=dict(bpm=bpm,music_seconds=beats*60/bpm,audio_seconds=frames/sr,notes_per_part=[len(part['notes']) for part in music['parts']],parts=stats,synth='FluidSynth',soundfont=soundfont.name,soundfont_sha256=hashlib.sha256(soundfont.read_bytes()).hexdigest(),reverb=False,chorus=False,effects=[],peak_before_gain=peak,output_peak=float(abs(mix).max()))
    (p/(base.name+'_render_settings.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path(__file__).parent/'configs/six_parts.yaml')
    parser.add_argument('--output',type=Path,default=Path('output'))
    parser.add_argument('--name',default='Jonathan_Marmor_six_parts_320bpm')
    parser.add_argument('--midi-only',action='store_true')
    parser.add_argument('--from-pulses',action='store_true',help='Begin at the 32 pulses that start the second movement.')
    parser.add_argument('--soundfont',type=Path,default=Path('/usr/share/sounds/sf2/TimGM6mb.sf2'))
    args=parser.parse_args()
    if not args.midi_only:
        for exe in ['fluidsynth','ffmpeg']:
            if not shutil.which(exe):parser.error(f'{exe} is required for audio; use --midi-only or install it.')
        if not args.soundfont.is_file():parser.error('Soundfont missing; specify --soundfont PATH.')
    if Path(args.name).name!=args.name or '.' in args.name:parser.error('--name must be a plain filename stem without dots.')
    config=yaml.safe_load(args.config.read_text())
    if not 1<=len(config['ensemble'])<=9:parser.error('Use 1–9 melodic parts (percussion channel is reserved).')
    if config.get('tempo_duration',4)!=4:parser.error('This renderer expects quarter-note BPM (tempo_duration: 4).')
    if config['tempo_bpm']<=0 or config['steps']<=0:parser.error('Tempo and steps must be positive.')
    args.output.mkdir(parents=True,exist_ok=True)
    music=generate(config, args.from_pulses);base=args.output/args.name
    (args.output/(args.name+'_notes.json')).write_text(json.dumps(music))
    render(music,base,not args.midi_only,args.soundfont)
    print(f'Wrote files to {args.output.resolve()}')

if __name__=='__main__':main()
