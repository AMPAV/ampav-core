import logging
from typing import Any, Iterator
import av
import av.audio.resampler
from pathlib import Path
from .schema.image import Image, SerializableImage

# so...ampav.core doesn't include numpy by default (since who knows what version
# some random tool will need), so we'll import it where it's actually used so
# if there are functions that don't need that functionality it won't bother
# loading it.

class ChunkedAudio:
    def __init__(self, filename: Path, stream: int,                 
                 sample_rate: int | None=None, 
                 channels: int | None=None):
        """Return s16 audio samples from a file in chunks

        Args:
            filename (Path): Source filename
            stream (int): Audio stream identifier from the file (usually 0)
            sample_rate (int | None, optional): desired sample rate. Defaults to pass through.
            channels (int | None, optional): desired number of channels. Defaults to pass through.
        """
        
        self.filename = filename
        # set up a resampler if we need to.
        input_container = av.open(filename)
        prototype_frame = next(input_container.decode(audio=stream))
        duration = input_container.duration / 1_000_000        
        input_container.close()
        resampler_params = {'format': 's16'}
        if channels is not None and prototype_frame.layout.nb_channels != channels:
            resampler_params['layout'] = av.AudioLayout('mono' if channels == 1 else 'stereo')
        else:
            channels = prototype_frame.layout.nb_channels
        if sample_rate is not None and prototype_frame.sample_rate != sample_rate:
            resampler_params['rate'] = sample_rate
        else:
            sample_rate = prototype_frame.sample_rate        

        self.resampler = av.audio.resampler.AudioResampler(**resampler_params)
        self.channels = channels
        self.sample_rate = sample_rate
        self.stream = stream
        logging.debug(f"channels: {prototype_frame.layout.nb_channels}->{channels}, sample_rate: {prototype_frame.sample_rate}->{sample_rate}, samples: {prototype_frame.sample_rate * duration}->{sample_rate*duration}")
        logging.debug(f"Resampler parameters: {resampler_params}")
        
        
    def __enter__(self):
        return self


    def get_chunks(self, chunk_duration: float, chunk_overlap: float=0) -> Iterator[tuple[float, Any]]:
        """the chunking iterator

        Args:
            chunk_duration (float): How large each chunk should be, in seconds
            chunk_overlap (float, optional): How much each chunk should overlap. Defaults to 0.

        Yields:
            Iterator[tuple[float, Any]]: The starting time of the samples, and the samples themselves
        """
        import numpy as np

        # Variation of the methodology originally implemented.  The chunks will
        # always be the chunk duration (except for the last, of course), but
        # the start time of the 2nd chunk and beyond will be chunk_overlap
        # seconds back.  We're going to just return the start time of the samples
        # and the samples themselves.
        
        target_sample_count = chunk_duration * self.sample_rate
        current_time = 0
        samples = []
        for frame in av.open(self.filename).decode(audio=self.stream):            
            out_frames = self.resampler.resample(frame)
            for out_frame in out_frames:              
                next_frame = out_frame.to_ndarray()[0]                
                samples.extend(next_frame)                
                if len(samples) >= target_sample_count:
                    logging.debug(f"Yielding chunk of {len(samples)} samples ({len(samples)/self.sample_rate} seconds).  Current time {current_time}")
                    yield current_time, np.array(samples, dtype=np.int16).astype(np.float32)/32768.0
                    current_time += len(samples) / self.sample_rate
                    # we have to rewind by chunk_overlap seconds, so let's pull them off the back
                    # and adjust the current time backwards...
                    if chunk_overlap:
                        samples = samples[-(chunk_overlap * self.sample_rate):]
                        current_time -= len(samples) / self.sample_rate
                    else:
                        samples = []
        if samples:
            # if we've buffered some chunks but didn't get enough data for a yield
            logging.debug(f"Final chunk of {len(samples)} samples, ({len(samples)/self.sample_rate} seconds). Current time: {current_time}")
            yield current_time, np.array(samples, dtype=np.int16).astype(np.float32) / 32768.0


    def get_fixed_chunks(self, chunk_length: int, pad: bool=False) -> Iterator[tuple[float, Any]]:
        """the fixed-length chunking iterator

        Args:
            chunk_length (int): How many samples per chunk
            pad (bool, optional): Whether or not to pad the last chunk

        Yields:
            Iterator[tuple[float, Any]]: The starting time of the samples, and the samples themselves
        """
        import numpy as np

        # Variation of the methodology originally implemented.  The chunks will
        # always be the chunk duration (except for the last, of course), but
        # the start time of the 2nd chunk and beyond will be chunk_overlap
        # seconds back.  We're going to just return the start time of the samples
        # and the samples themselves.
        
        current_time = 0
        samples = []
        for frame in av.open(self.filename).decode(audio=self.stream):            
            out_frames = self.resampler.resample(frame)
            for out_frame in out_frames:              
                next_frame = out_frame.to_ndarray()[0]                                
                samples.extend(next_frame)                
                while len(samples) >= chunk_length:
                    # get our correct-sized chunk and save the remainder
                    this_chunk = samples[:chunk_length]
                    samples = samples[chunk_length:]

                    logging.debug(f"Yielding chunk of {len(this_chunk)} samples ({len(this_chunk)/self.sample_rate} seconds).  Current time {current_time}")
                    yield current_time, np.array(this_chunk, dtype=np.int16).astype(np.float32)/32768.0
                    current_time += len(this_chunk) / self.sample_rate


        if samples:
            # if we've buffered some chunks but didn't get enough data for a yield
            if len(samples) < chunk_length and pad:
                samples = samples + [0] * (chunk_length - len(samples))
            logging.debug(f"Final chunk of {len(samples)} samples, ({len(samples)/self.sample_rate} seconds). Current time: {current_time}")
            yield current_time, np.array(samples, dtype=np.int16).astype(np.float32) / 32768.0

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def load_and_resample_audio_file(filename: Path, stream: int, 
                                 sample_rate: int | None=None, 
                                 channels: int | None =None) ->tuple[int, int, Any]:
    """Load an audio file into memory as s16, optionally resampling it

    Args:
        filename (Path): Audio source file
        stream (int): Audio stream id (usually 0)
        sample_rate (int | None, optional): desired sample reate. Defaults to pass through.
        channels (int | None, optional): desired number of channels. Defaults to pass through.

    Returns:
        tuple[int, int, Any]: number of channels, sample rate, and the samples themselves
    """

    
    import numpy as np
    
    # set up a resampler
    input_container = av.open(filename)
    prototype_frame = next(input_container.decode(audio=stream))
    resampler = None
    resampler_params = {'format': 's16'}
    if channels is not None and prototype_frame.layout.nb_channels != channels:
        resampler_params['layout'] = av.AudioLayout('mono' if channels == 1 else 'stereo')
    else:
        channels = prototype_frame.layout.nb_channels
    if sample_rate is not None and prototype_frame.sample_rate != sample_rate:
        resampler_params['rate'] = sample_rate
    else:
        sample_rate = prototype_frame.sample_rate
    
    resampler = av.audio.resampler.AudioResampler(**resampler_params)
    duration = input_container.duration / 1_000_000
    logging.debug(f"channels: {prototype_frame.layout.nb_channels}->{channels}, sample_rate: {prototype_frame.sample_rate}->{sample_rate}, samples: {prototype_frame.sample_rate * duration}->{sample_rate*duration}")
    logging.debug(f"Resampler parameters: {resampler_params}") 
    chunks = []
    for frame in input_container.decode(audio=stream):
        out_frames = resampler.resample(frame)
        for out_frame in out_frames:
            chunks.extend(out_frame.to_ndarray()[0])

    samples = np.append(np.array([], dtype=np.int16), chunks).astype(np.float32) / 32768.0
    #print(samples.shape, samples.dtype)
    input_container.close()
    return channels, sample_rate, samples


def get_frames_from_video(filename: Path, stream: int, frame_list: list[float]) -> Iterator[tuple[float, Image]]:
    """Return a dictionary of images keyed by the time and the value is the 
       image itself, or None if no suitable image could be found.

    Args:
        filename (Path): Video file
        stream (int): Video stream index in the file
        frame_list (list[float]): List of time offsets for the images

    Returns:
        Iterator[tuple[float, Image]]: Images found at the times, or None if there's no image there.
    """
    container = av.open(filename)
    stream: av.VideoStream = container.streams.video[stream]
    # sort the offsets so I'm only seeking forward and convert them to presentation
    # timestamps (PTS) by dividing by the time base
    for frame_time in sorted(frame_list):
        frame_pts = int(frame_time / stream.time_base)
        # seek to the nearest keyframe (any_frame=False) that's 
        # before (backward=True) our desired PTS.  
        container.seek(frame_pts, stream=stream, any_frame=False, backward=True)
        # decode forward until we find our actual frame...
        for frame in container.decode(stream):
            if frame.pts >= frame_pts:
                # this is our stop.
                yield (frame_time, Image(filename=f"{filename.name}_{frame_time}.png",
                                            image=frame.to_image()))              
                break
        else:
            logging.warning(f"Skipping frame at pts {frame_pts} because it could not be found.")
            yield (frame_time, None)        
    container.close()
    