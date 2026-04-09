from pydantic import Field
from typing import Annotated, Any
from annotated_types import Len, Literal
from pathlib import Path
from .basemodel import AmpAVBaseModel
import av
import av.container
import argparse

class AudioStream(AmpAVBaseModel):
    bit_rate: int = Field(0, description="Stream bit rate")
    channels: int = Field(0, description="Number of channels in the field")
    codec_name: str = Field('unknown', description='Codec name')
    codec_profile: str | None = Field(None, description="Codec profile")
    codec_tag: str = Field('unknown', description="Codec tag")
    duration: float = Field(0, description="Stream duration, in seconds")
    index: int = Field(-1, description="Stream container index")
    layout: str = Field('unknown', description="Channel layout name")
    metadata: dict[str, Any] = Field(default_factory=dict,
                                     description="User-defined stream metadata")
    sample_rate: int = Field(0, description="Sample rate")
    start_time: float | None = Field(0, description="Stream start time")    


class VideoStream(AmpAVBaseModel):
    @staticmethod
    def fraction_factory(num=1, den=1):
        return [num, den]
    
    bit_rate: int = Field(0, description="Stream bit rate")
    bits_per_sample: int = Field(0, description="Bits per coded sample")
    codec_name: str = Field('unknown', description='Codec name')
    codec_profile: str | None = Field(None, description="Codec profile")
    codec_tag: str = Field('unknown', description="Codec tag")
    display_aspect_ratio: Annotated[list[int], Len(min_length=2, max_length=2)] = Field(default_factory=fraction_factory,
                                                                                       description="Display Aspect Ratio") 
    duration: float = Field(0, description="Stream duration, in seconds")
    frame_rate: Annotated[list[int], Len(min_length=2, max_length=2)] = Field(default_factory=fraction_factory,
                                                                              description="Frame rate")
    height: int = Field(0, description="Frame height")
    index: int = Field(-1, description="Stream container index")
    metadata: dict[str, Any] = Field(default_factory=dict,
                                     description="User-defined stream metadata")
    pixel_format: str = Field('unknown', description="Pixel format name")
    sample_aspect_ratio: Annotated[list[int], Len(min_length=2, max_length=2)] = Field(default_factory=fraction_factory,
                                                                                       description="Sample Aspect Ratio")    
    start_time: float | None = Field(0, description="Stream start time")
    width: int = Field(0, description="Frame width")
    

class SubtitleStream(AmpAVBaseModel):
    pass


class Streams(AmpAVBaseModel):
    audio: list[AudioStream] = Field(default_factory=list,
                                     description="Audio Streams")
    video: list[VideoStream] = Field(default_factory=list,
                                     description="Video Streams")
    subtitle: list[SubtitleStream] = Field(default_factory=list,
                                     description="Subtitle Streams")
    

class AVMetadata(AmpAVBaseModel):
    """Technical metadata for a file"""
    ampav_format: Literal['avmetadata'] = 'avmetadata'
    ampav_format_version: Literal[1] = 1
    bit_rate: int = Field(0, description="Overall media bitrate")
    duration: float = Field(0, description="File duration, in microseconds")
    format_name: str = Field('Unknown', description="Format name")
    format_long_name: str = Field('Unknown', description="Format's long name")
    metadata: dict[str, Any] = Field(default_factory=dict, 
                                     description="User-defined container metadata")
    size: int = Field(0, description="File size")
    start_time: int | None = Field(0, description="Media start time, in microseconds")
    streams: Streams = Field(default_factory=Streams,
                             description="Streams in the container file")
    

    @staticmethod
    def _safe_getattr(o: object, k: str) -> Any:
        this, *rest = k.split('.')
        try:
            v = getattr(o, this)
        except Exception as e:
            v = None            
        if rest and v is not None:
            v = AVMetadata._safe_getattr(v, '.'.join(rest))
        return v


    @staticmethod
    def _getattrs(o: object, attrs: list[str]) -> dict:
        data = {}
        for k in attrs:
            spec = k.split('!')
            if len(spec) == 1:
                spec.append(spec[0])
            data_key, object_key = spec
            data[data_key] = AVMetadata._safe_getattr(o, object_key)
        return data


    @classmethod
    def from_file(cls, file: Path):        
        m = av.container.open(file)
        data = AVMetadata._getattrs(m,
                                    ['bit_rate', 'duration', 
                                     'format_name!format.name',
                                     'format_long_name!format.long_name', 
                                     'metadata', 'size', 'start_time'])
        
        data['streams'] = {'audio': [], 'video': [], 'subtitle': []}
        for s in m.streams.audio:
            sdata = AVMetadata._getattrs(s, 
                                         ['bit_rate', 'channels', 
                                          'codec_name!name', 'codec_profile!profile',
                                          'codec_tag', 'duration', 'index', 
                                          'layout!layout.name', 'metadata', 
                                          'sample_rate', 'start_time'])
            sdata['duration'] *= AVMetadata._safe_getattr(s, 'time_base')
            data['streams']['audio'].append(sdata)

        for s in m.streams.video:
            sdata = AVMetadata._getattrs(s,
                                         ['bit_rate', 'bits_per_sample!bits_per_coded_sample',
                                          'codec_name!name', 'codec_profile!profile',
                                          'codec_tag', 'display_aspect_ratio', 'duration', 
                                          'frame_rate!average_rate', 'height', 'index', 
                                          'metadata', 'pixel_format!pix_fmt', 
                                          'sample_aspect_ratio', 'start_time', 
                                          'type', 'width'])
            sdata['duration'] *= float(getattr(s, 'time_base'))
            for k in ('display_aspect_ratio', 'frame_rate', 'sample_aspect_ratio'):
                sdata[k] = [sdata[k].numerator, sdata[k].denominator]
            data['streams']['video'].append(sdata)

        return AVMetadata(**data)



def cli_probe_media():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help="Filename to probe")
    args = parser.parse_args()
    print(AVMetadata.from_file(args.filename).model_dump_yaml())
