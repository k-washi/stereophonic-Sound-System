import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# ------------

from utils.config import configInit
Conf = configInit()
logger = Conf.setLogger(__name__)

from acoustic.acousticSignalProc import AudioDevice, convNp2pa, convPa2np

# ------------

import pyaudio
import keyboard
import scipy
import numpy as np

class MicAudioStream():
  def __init__(self):
    self.pAudio = pyaudio.PyAudio()
    self.micInfo = AudioDevice(Conf.MicID)
    self.outInfo = AudioDevice(Conf.OutpuID)
    self.format = pyaudio.paFloat32

  
  def callback(self, in_data, frame_count, time_info, status):
    try:
      pyAudio 2 numpy
      data = convPa2np(scipy.fromstring(in_data, scipy.float32), channelNum=self.micInfo.micChannelNum)
      data[0] = 0
      data = convNp2pa(data)
      print(data.shape)

      #numpy 2 pyAudio
      out_data = data.astype(np.float32).tostring()
    except KeyboardInterrupt:
      pass

    
    return (out_data, pyaudio.paContinue)
  

  
  def start(self):
    
    """
    rate – Sampling rate
    channels – Number of channels
    format – Sampling size and format. See PortAudio Sample Format.
    input – Specifies whether this is an input stream. Defaults to False.
    output – Specifies whether this is an output stream. Defaults to False.
    input_device_index – Index of Input Device to use. Unspecified (or None) uses default device. Ignored if input is False.
    output_device_index – Index of Output Device to use. Unspecified (or None) uses the default device. Ignored if output is False.
    frames_per_buffer – Specifies the number of frames per buffer.
    start – Start the stream running immediately. Defaults to True. In general, there is no reason to set this to False.
    input_host_api_specific_stream_info – Specifies a host API specific stream information data structure for input.
    output_host_api_specific_stream_info – Specifies a host API specific stream information data structure for output.
    stream_callback –Specifies a callback function for non-blocking (callback) operation. Default is None, which indicates blocking operation (i.e., Stream.read() and Stream.write()). To use non-blocking operation, specify a callback that conforms to the following signature:
    callback(in_data,      # recorded data if input=True; else None
            frame_count,  # number of frames
            time_info,    # dictionary
            status_flags) # PaCallbackFlags
    time_info is a dictionary with the following keys: input_buffer_adc_time, current_time, and output_buffer_dac_time; see the PortAudio documentation for their meanings. status_flags is one of PortAutio Callback Flag.
    The callback must return a tuple:
    (out_data, flag)
    out_data is a byte array whose length should be the (frame_count * channels * bytes-per-channel) if output=True or None if output=False. flag must be either paContinue, paComplete or paAbort (one of PortAudio Callback Return Code). When output=True and out_data does not contain at least frame_count frames, paComplete is assumed for flag.
    """
    self.stream = self.pAudio.open(
      format = self.format,
      rate = self.micInfo.samplingRate,
      channels = self.micInfo.micChannelNum,
      input = True,
      output = True,
      input_device_index = Conf.MicID,
      output_device_index = Conf.OutpuID,
      stream_callback = self.callback
    )

    self.stream.start_stream()

  def stop(self):
    while st.stream.is_active():
      pass
      #logger.debug("active")
  
    st.stream.start_stream()
    st.stream.close()
    st.close()

  
  def close(self):
    self.pAudio.terminate()
    logger.debug("Close proc")

if __name__ == "__main__":
  st = MicAudioStream()
  st.start()
  try:
    pass
  finally:
    st.stop()
  

  
