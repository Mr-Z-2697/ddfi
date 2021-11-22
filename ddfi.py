import os,sys
import argparse
import subprocess
toolsFolder=f'{os.path.dirname(os.path.realpath(__file__))}\\tools\\'
sys.path.append(toolsFolder)
class args:
    pass
parser = argparse.ArgumentParser(description='an animation auto duplicated frame remove and frame interpolate script, uses ffmpeg, mkvextract, and vapoursynth.',formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i','--input',required=True,type=str,help='source file, any format ffmpeg can decode\n ')
parser.add_argument('-o','--output',required=False,type=str,help='output file, default \"input file\"_interp.mkv\n ')
parser.add_argument('-tf','--temp_folder',required=False,type=str,help='temp folder, default \"output file\"_tmp\\\n ')
parser.add_argument('-st','--start_time',required=False,type=str,help='cut input video from this time, format h:mm:ss.nnn or seconds\n ')
parser.add_argument('-et','--end_time',required=False,type=str,help='cut input video end to this time, format h:mm:ss.nnn or seconds\n ')
parser.add_argument('-as','--audio_stream',required=False,type=str,help='set audio stream index, starts from 0, \n\"no\" means don\'t output audio, and is the default\n ',default='no')
parser.add_argument('-q','--output_crf',required=False,type=int,help='output video crf value, interger. if a codec don\'t has -crf option is used, \n--ffmpeg_params_output can be used as a workaround. default 18\n ')
parser.add_argument('-qi','--intermedia_quality_params',required=False,type=str,help='parameters associated to intermedia video quality. \nalmost useless now. default \"-crf 27 -s 16x16\"\n ')
parser.add_argument('-vc','--video_codec',required=False,type=str,help='output video codec, use the name in ffmpeg, \nwill be constrained by output format. default libx265\n ')
parser.add_argument('-ac','--audio_codec',required=False,type=str,help='output audio codec, similar to -vc. default libopus\n ')
parser.add_argument('-al','--audio_channel_layout',required=False,type=str,help='output audio channel layout, \nuse the name in ffmpeg. default stereo\n ')
parser.add_argument('-ab','--audio_bitrate',required=False,type=str,help='output audio bitrate, use it like in ffmpeg. default 128k\n ')
parser.add_argument('-cm','--customize_mpdecimate_opts',required=False,type=str,help='set ffmpeg mpdecimate filter options. write it like how you use filter \nin ffmpeg. default \"max=2\"\n ')
parser.add_argument('--ffmpeg_params_output',required=False,type=str,help='other ffmpeg parameters used in final step, \nuse it carefully. default \"-map_metadata -1 -map_chapters -1\"\n ')
parser.add_argument('-scd',required=False,type=str,help='scene change detect method, \"misc\", \"mv\" or \"none\", default misc',default='misc')
parser.add_argument('-thscd',required=False,type=str,help='thscd1&2 of core.mv.SCDetection, default 200,130',default='200,130')
parser.add_argument('--dont_be_scared',required=False,type=str,help='i know you are seeing a lot of arguments up there, but don\'t be scared! \nthe important ones are only -i, -o, -as, [-st], [-et] \nand what this argument do? give a number or just right click open with blahblah')
parser.parse_args(sys.argv[1:],args)

inFile=args.input
if args.dont_be_scared is not None:
    outFile=os.path.splitext(inFile)[0]+'_=w=.mkv' if args.output is None else os.path.splitext(args.output)[0]+'_=w='+os.path.splitext(args.output)[1]
else:
    outFile=os.path.splitext(inFile)[0]+'_interp.mkv' if args.output is None else args.output
tmpFolder=os.path.splitext(outFile)[0]+'_tmp\\' if args.temp_folder is None else args.temp_folder+'\\'
#tmpFolder+='\\' if tmpFolder[-1] is not '\\' else ''

ffss='' if args.start_time is None else f'-ss {args.start_time}'
ffto='' if args.end_time is None else f'-to {args.end_time}'
ffau='-an' if args.audio_stream == 'no' else f'-map a:{args.audio_stream}'
ffau2='-an' if args.audio_stream == 'no' else f'-map 1:a:0'
crfo=18 if args.output_crf is None else args.output_crf
qofim='-crf 27 -s 16x16' if args.intermedia_quality_params is None else args.intermedia_quality_params
codecov='-c:v libx265 -preset 6 -x265-params sao=0:rect=0:strong-intra-smoothing=0:open-gop=0:b-intra=1:weightb=1:aq-mode=1:aq-strength=0.8:ctu=32:rc-lookahead=60' if args.video_codec is None else f'-c:v {args.video_codec}'
codecoa='-c:a libopus' if args.audio_codec is None else f'-c:a {args.audio_codec}'
clo='-channel_layout stereo' if args.audio_channel_layout is None else f'-channel_layout {args.audio_channel_layout}'
abo='-b:a 128k' if args.audio_bitrate is None else f'-b:a {args.audio_bitrate}'
ffparamo='-map_metadata -1 -map_chapters -1' if args.ffmpeg_params_output is None else args.ffmpeg_params_output
mpdopts='2' if args.customize_mpdecimate_opts is None else args.customize_mpdecimate_opts

if args.scd not in ['misc','mv','none']:
    raise ValueError('scd must be misc, mv or none.')
thscd1,thscd2=args.thscd.split(',')

tmpDedup=os.path.abspath(tmpFolder+'dedup_intermedia.mkv')
tmpTSV2O=os.path.abspath(f'{tmpFolder}tsv2o.txt')
tmpTSV2N=os.path.abspath(f'{tmpFolder}tsv2nX8.txt')

ffpath=mmgpath=dllpath=toolsFolder
vspipepath=toolsFolder+'python-vapoursynth-plugins\\'

try:
    import vapoursynth
except:
    raise RuntimeError('vapoursynth environment is needed, it seems like you don\'t have one.')

def newTSgen():
    if not os.path.exists(tmpTSV2O):
        mEx=f'\"{mmgpath}mkvextract.exe\" \"{tmpDedup}\" timestamps_v2 0:\"{tmpTSV2O}\"'
        print(mEx)
        subprocess.run(mEx,shell=True)
    
    ts_o=list()
    ts_new=list()
    outfile=open(tmpTSV2N,'w',encoding='utf-8')
    f=open(tmpTSV2O,'r',encoding='utf-8')
    for line in f:
        ts_o.append(line)
    #print(ts_o)
    
    for x in range(1,len(ts_o)-1):
        ts_new.append(str(float(ts_o[x])))
        for i in range(1,8):
            ts_new.append( str(float(ts_o[x]) + (float(ts_o[x+1])-float(ts_o[x]))/8*i) )
    #print(ts_new)
    print('# timestamp format v2',file=outfile)
    for x in range(len(ts_new)):
        print(ts_new[x],file=outfile)
    print(ts_o[len(ts_o)-1],file=outfile)
    f.close()
    outfile.close()

def vpyGen():
    scd=f'sup = core.mv.Super(clip)\nbw = core.mv.Analyse(sup,isb=True)\nclip = core.mv.SCDetection(clip,bw,thscd1={thscd1},thscd2={thscd2})' if args.scd=='mv' else 'clip = core.misc.SCDetect(clip)' if args.scd=='misc' else ''
    script='''import vapoursynth as vs
from vapoursynth import core
core.num_threads=8
core.max_cache_size=32768
clip = core.raws.Source(r\"-\")
clip = core.std.AssumeFPS(clip,fpsnum=10,fpsden=1)
%s
clip = core.resize.Bicubic(clip,format=vs.RGBS,matrix_in=1)
clip = core.rife.RIFE(clip,model=0,sc=True)
clip = core.rife.RIFE(clip,model=0,sc=True,uhd=True)
clip = core.rife.RIFE(clip,model=0,sc=True,uhd=True)
clip = core.resize.Bicubic(clip,format=vs.YUV420P10,matrix=1)
clip = core.vfrtocfr.VFRToCFR(clip,r"%s",192000,1001,True)
sup = core.mv.Super(clip)
fw = core.mv.Analyse(sup)
bw = core.mv.Analyse(sup,isb=True)
clip = core.mv.FlowFPS(clip,sup,bw,fw,60,1)
clip.set_output()
''' % (scd,tmpTSV2N)

    vpy=open(f'{tmpFolder}interpX8.vpy','w',encoding='utf-8')
    print(script,file=vpy)
    vpy.close()

if not os.path.exists(inFile):
    print('input file isn\'t exist')
    exit()
if os.path.exists(outFile):
    if input('output file exists, continue? (y/n) ')=='y':
        pass
    else:
        exit()
if os.path.exists(tmpFolder):
    if input('temp folder exists, continue? (y/n) ')=='y':
        pass
    else:
        exit()
else:
    os.mkdir(tmpFolder)

if not os.path.exists(tmpDedup):
    ff_intermedia=f'\"{ffpath}ffmpeg.exe\" {ffss} {ffto} -i \"{inFile}\" -vf mpdecimate={mpdopts} -map 0:v:0 {ffau} {clo} -c:a flac -c:v libx264 {qofim} -preset 1 -y \"{tmpFolder}dedup.mkv\"'
    print(ff_intermedia)
    subprocess.run(ff_intermedia,shell=True)
    os.rename(f'{tmpFolder}dedup.mkv',tmpDedup)

newTSgen()
vpyGen()
cmdinterp=f'\"{ffpath}ffmpeg.exe\" -loglevel 0 {ffss} {ffto} -i \"{inFile}\" -vf mpdecimate={mpdopts},setpts=N/(30*TB) -map 0:v:0 -r 30 -pix_fmt yuv420p10le -strict -1 -f yuv4mpegpipe - | \"{vspipepath}vspipe.exe\" -y \"{tmpFolder}interpX8.vpy\" - | \"{ffpath}ffmpeg.exe\" -i - -i \"{tmpDedup}\" -map 0:v:0 {ffau2} -crf {crfo} {codecov} {codecoa} {abo} {ffparamo} \"{outFile}\" -y'
print(cmdinterp)
subprocess.run(cmdinterp,shell=True)
