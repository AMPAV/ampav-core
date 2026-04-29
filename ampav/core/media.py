from typing import Any, Iterator
import av
import av.audio.resampler
from pathlib import Path

# so...ampav.core doesn't include numpy by default (since who knows what version
# some random tool will need), so we'll import it where it's actually used so
# if there are functions that don't need that functionality it won't bother
# loading it.

class ChunkedAudio:
    def __init__(self, filename: Path, stream: int,                 
                 sample_rate: int | None=None, 
                 channels: int | None=None):
        """Resample and chunk up audio files"""
        self.filename = filename
        # set up a resampler if we need to.
        input_container = av.open(filename)
        prototype_frame = next(input_container.decode(audio=stream))
        input_container.close()
        resampler_params = {}
        if channels is not None and prototype_frame.layout.nb_channels != channels:
            resampler_params = {'layout': av.AudioLayout('mono' if channels == 1 else 'stereo')}
        else:
            channels = prototype_frame.layout.nb_channels
        if sample_rate is not None and prototype_frame.sample_rate != sample_rate:
            resampler_params = {'rate': sample_rate}
        else:
            sample_rate = prototype_frame.sample_rate
        self.resampler = av.audio.resampler.AudioResampler(format='s16', **resampler_params)                                                                     
        self.channels = channels
        self.sample_rate = sample_rate
        self.stream = stream
        

    def __enter__(self):
        return self


    def get_chunks(self, chunk_duration: float, chunk_overlap: float=0) -> Iterator[tuple[tuple[float, float], Any]]:
        """Get the next chunk of audio with the desired
           duration.  Return the actual duration and samples"""        
        import numpy as np
        chunk_duration = chunk_duration - chunk_overlap * 2
        samples_to_read = (chunk_duration + chunk_overlap) * self.sample_rate
        overlap_samples = chunk_overlap * self.sample_rate        
        samples = []                
        start_position = 0
        overlap_offset = 0
        samples_read = 0
        for frame in av.open(self.filename).decode(audio=self.stream):            
            out_frames = self.resampler.resample(frame)
            for out_frame in out_frames:                
                next_frame = out_frame.to_ndarray()[0]
                samples.extend(next_frame)
                samples_read += len(next_frame)            
                if samples_read >= samples_to_read:
                    yield (start_position, overlap_offset), np.array(samples, dtype=np.int16).astype(np.float32)/32768.0
                    # take the overlap samples and move them to the front                
                    
                    if overlap_samples:
                        samples = samples[-overlap_samples:]                
                    else:
                        samples = []
                    overlap_offset = len(samples) / self.sample_rate
                    start_position += (samples_read - overlap_offset) / self.sample_rate
                    samples_read = 0

        if samples:
            # if we've buffered some chunks but didn't get enough data for a yield
            yield (start_position, overlap_offset), np.array(samples, dtype=np.int16).astype(np.float32) / 32768.0


    def __exit__(self, exc_type, exc_value, traceback):
        pass


def load_and_resample_audio_file(filename: Path, stream: int, 
                                 sample_rate: int | None=None, 
                                 channels: int | None =None) ->tuple[int, int, Any]:
    """
    Load a media file and return a numpy array of the content
    
    :param filename: Description
    :type filename: Path
    :param sample_rate: Description
    :type sample_rate: int
    :param channels: Description
    :type channels: int
    :param stream: Description
    :type stream: int
    """
    import numpy as np
    
    # set up a resampler
    input_container = av.open(filename)
    prototype_frame = next(input_container.decode(audio=stream))
    resampler = None
    resampler_params = {}
    if channels is not None and prototype_frame.layout.nb_channels != channels:
        resampler_params = {'layout': av.AudioLayout('mono' if channels == 1 else 'stereo')}
    else:
        channels = prototype_frame.layout.nb_channels
    if sample_rate is not None and prototype_frame.sample_rate != sample_rate:
        resampler_params = {'rate': sample_rate}
    else:
        sample_rate = prototype_frame.sample_rate
    resampler = av.audio.resampler.AudioResampler(format='s16', **resampler_params)                                                 
        
    chunks = []
    for frame in input_container.decode(audio=stream):
        out_frames = resampler.resample(frame)
        for out_frame in out_frames:
            chunks.extend(out_frame.to_ndarray()[0])

    samples = np.append(np.array([], dtype=np.int16), chunks).astype(np.float32) / 32768.0
    #print(samples.shape, samples.dtype)
    return channels, sample_rate, samples