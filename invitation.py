"""Portable 1080p invitation renderer. No Canva or company credentials required."""
import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent


def handle_value(value):
    value = value.strip().lstrip('@')
    if not re.fullmatch(r'[A-Za-z0-9_]{1,15}', value):
        raise ValueError('Handle must contain 1–15 letters, digits or underscores')
    return value


def font(size, weight=700):
    f = ImageFont.truetype(str(ROOT/'assets/fonts/Inter[opsz,wght].ttf'), size)
    f.set_variation_by_axes([14, weight])
    return f


def avatar_image(row):
    if row.get('avatar_path'):
        with Image.open(row['avatar_path']) as im:
            return ImageOps.exif_transpose(im).convert('RGB')
    url = row.get('avatar_url')
    if not url:
        response = requests.get('https://api.fxtwitter.com/'+row['handle'], timeout=25)
        response.raise_for_status()
        user = response.json()['user']
        if user['screen_name'].lower() != row['handle'].lower():
            raise ValueError('Profile handle mismatch')
        url = user['avatar_url'].replace('_normal.', '.')
    if not url.startswith('https://'):
        raise ValueError('Avatar URL must use HTTPS')
    response = requests.get(url, timeout=25)
    response.raise_for_status()
    with Image.open(io.BytesIO(response.content)) as im:
        return ImageOps.exif_transpose(im).convert('RGB')


def make_overlay(row, cfg, output):
    # Rasterize font outlines at twice output resolution for clean antialiasing.
    scale = 2
    layer = Image.new('RGBA', (1080*scale, 1920*scale))
    draw = ImageDraw.Draw(layer)
    boxes = []
    for spec in cfg['texts']:
        text = ('@'+row['handle']).upper() if spec['text'] == '{handle}' else spec['text']
        size = spec['size']*scale
        f = font(size, spec.get('weight',700))
        while draw.textlength(text, font=f) > spec['max_width']*scale and size > 12*scale:
            size -= 1
            f = font(size, spec.get('weight',700))
        if draw.textlength(text, font=f) > spec['max_width']*scale:
            raise ValueError('Text exceeds available width: '+text)
        xy = (spec['x']*scale, spec['y']*scale)
        anchor = spec.get('anchor','mt')
        box = draw.textbbox(xy,text,font=f,anchor=anchor)
        if not (210*scale <= box[0] < box[2] <= 855*scale and 415*scale <= box[1] < box[3] <= 1390*scale):
            raise ValueError('Text would touch card frame: '+text)
        draw.text(xy,text,font=f,fill='white',anchor=anchor)
        boxes.append({'text':text,'box':[v/scale for v in box]})
    avatar = avatar_image(row)
    native_size = avatar.size
    x,y,diameter = cfg['avatar']
    avatar = ImageOps.fit(avatar,(diameter*scale,diameter*scale),method=Image.Resampling.LANCZOS)
    mask = Image.new('L',avatar.size)
    ImageDraw.Draw(mask).ellipse((0,0,diameter*scale-1,diameter*scale-1),fill=255)
    layer.paste(avatar,(x*scale,y*scale),mask)
    for spec in cfg['marks']:
        mark = Image.open(ROOT/spec['file']).convert('RGBA')
        mark = mark.resize((spec['width']*scale,spec['height']*scale),Image.Resampling.LANCZOS)
        layer.alpha_composite(mark,(spec['x']*scale,spec['y']*scale))
    draw.line((496*scale,1104*scale,584*scale,1104*scale),fill=(255,255,255,210),width=2*scale)
    layer = layer.resize((1080,1920),Image.Resampling.LANCZOS)
    layer.save(output)
    return {'avatar_source_size':native_size,'avatar_below_display_resolution':min(native_size)<diameter,
            'text_boxes':boxes,'alpha_bounds':layer.getbbox()}


def run(args):
    return subprocess.check_output(args,stderr=subprocess.PIPE)


def audio_hash(path):
    return run(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-']).decode().strip()


def verify(path):
    run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
    probe=json.loads(run(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_type,width,height,nb_frames,r_frame_rate','-of','json',str(path)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    if (video['width'],video['height'],int(video['nb_frames']),video['r_frame_rate']) != (1080,1920,268,'30/1'):
        raise ValueError('Unexpected output dimensions/frame count')
    if audio_hash(path) != audio_hash(ROOT/'assets/original.mp4'):
        raise ValueError('Audio differs from original')
    return {'probe':probe,'original_audio_packet_hash_match':True,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def render(row,cfg,out,overwrite=False,crf=18):
    handle=handle_value(row['handle'])
    row=dict(row,handle=handle)
    video=out/('Invitation_'+handle+'_1080p.mp4')
    if video.exists() and not overwrite:
        raise FileExistsError(str(video)+' already exists; pass --overwrite to replace')
    overlay=out/'overlays'/(handle+'.png')
    qa=make_overlay(row,cfg,overlay)
    filters='[1:v]format=rgba,fade=t=in:st=5.933333:d=0.4:alpha=1[card];[0:v][card]overlay=0:0:shortest=1[v]'
    run(['ffmpeg','-v','error','-y','-i',str(ROOT/'assets/background.mp4'),'-loop','1','-framerate','30','-i',str(overlay),'-i',str(ROOT/'assets/original.mp4'),'-filter_complex_threads','1','-filter_complex',filters,'-map','[v]','-map','2:a:0','-t','8.933333','-c:v','libx264','-threads','2','-preset','fast','-crf',str(crf),'-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(video)])
    qa.update(verify(video))
    qa['handle']=handle
    qa['brand_marks']='Original preview-derived marks; replace with high-resolution PNGs when available'
    (out/'qa'/(handle+'.json')).write_text(json.dumps(qa,indent=2),encoding='utf-8')
    run(['ffmpeg','-v','error','-y','-ss','8','-i',str(video),'-frames:v','1',str(out/'qa'/(handle+'.png'))])
    print(handle+': verified 1080x1920, 268 frames, original audio'+(' (small source avatar)' if qa['avatar_below_display_resolution'] else ''),flush=True)
    return qa


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--handle');group.add_argument('--csv',type=Path)
    parser.add_argument('--avatar',type=Path,help='Local avatar for --handle; avoids all network requests')
    parser.add_argument('--output',type=Path,default=ROOT/'output')
    parser.add_argument('--config',type=Path,default=ROOT/'template.json')
    parser.add_argument('--workers',type=int,choices=range(1,5),default=2)
    parser.add_argument('--crf',type=int,choices=range(14,24),default=18)
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    for binary in ['ffmpeg','ffprobe']:
        if not shutil.which(binary):parser.error(binary+' not found; install FFmpeg and add it to PATH')
    if args.avatar and not args.handle:parser.error('--avatar requires --handle; use avatar_path column for CSV')
    if args.handle:
        rows=[{'handle':handle_value(args.handle),'avatar_path':str(args.avatar.resolve()) if args.avatar else ''}]
    else:
        with args.csv.open(encoding='utf-8-sig',newline='') as source:rows=list(csv.DictReader(source))
        for row in rows:
            row['handle']=handle_value(row['handle'])
            if row.get('avatar_path'):row['avatar_path']=str((args.csv.resolve().parent/row['avatar_path']).resolve())
    if not rows:parser.error('CSV has no recipients')
    if len({row['handle'].lower() for row in rows})!=len(rows):parser.error('Duplicate handles in CSV')
    cfg=json.loads(args.config.read_text(encoding='utf-8'))
    for folder in [args.output,args.output/'overlays',args.output/'qa']:folder.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results=list(pool.map(lambda r:render(r,cfg,args.output,args.overwrite,args.crf),rows))
    (args.output/'manifest.json').write_text(json.dumps({'status':'verified','count':len(results),'results':results},indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
