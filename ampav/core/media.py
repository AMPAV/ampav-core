import argparse
import av
import av.container
from fractions import Fraction
from pathlib import Path
import yaml

def probe_media(filename: Path) -> dict:
    """Return the media characteristics of the given file"""
    m = av.container.open(filename)

    metadata = {
        'streams': {'audio': [],
                    'video': []}
    }
    for k in ('bit_rate', 'duration', 'file', 'metadata', 
              'name', 'size', 'start_time'):
        metadata[k] = getattr(m, k)
    metadata['duration'] = metadata['duration'] / 1_000_000

    metadata['format'] = {}
    
    for k in ('extensions', 'name', 'long_name', 'flags'):
        metadata['format'][k] = getattr(m.format, k)
    metadata['format']['extensions'] = list(metadata['format']['extensions'])

    # audio streams
    for s in m.streams.audio:
        sd = {}
        metadata['streams']['audio'].append(sd)
        # gather data
        for k in ('bit_rate', 'channels', 'codec_tag', 'duration',
                  'index', 'language', 'metadata', 'name', 'profile',
                  'sample_rate', 'start_time'):
            sd[k] = getattr(s, k)
                
        sd['format'] = {}
        for k in ('bits', 'bytes', 'name'):
            sd['format'][k] = getattr(s.format, k)

        sd['layout'] = {}
        for k in ('name', 'nb_channels'):
            sd['layout'][k] = getattr(s.layout, k)
        
        sd['layout']['channels'] = []
        for i in range(s.layout.nb_channels):
            l = {}
            for k in ('name', 'description'):
                l[k] = getattr(s.layout.channels[i - 1], k)
            sd['layout']['channels'].append(l)

        # fixup values...
        sd['duration'] *= float(getattr(s, 'time_base'))
        
    # video streams
    for s in m.streams.video:        
        sd = {}
        metadata['streams']['video'].append(sd)
        for k in ('bit_rate', 'bits_per_coded_sample',
                  'codec_tag', 'duration', 
                  'height', 'index', 'language', 
                  'metadata', 'name', 'pix_fmt', 'profile',
                  'start_time', 'type', 'width'):
            sd[k] = getattr(s, k)
        sd['duration'] *= float(getattr(s, 'time_base'))

        for x in ('sample_aspect_ratio', 'display_aspect_ratio', 'average_rate'):
            v: Fraction = getattr(s, x)
            sd[x] = {'numerator': v.numerator,
                     'denominator': v.denominator,
                     'value': float(v)}

    return metadata


def media_to_wav():
    ...


def cli_probe_media():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help="Filename to probe")
    args = parser.parse_args()
    print(yaml.safe_dump(probe_media(args.filename)))
