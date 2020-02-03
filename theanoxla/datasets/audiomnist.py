import os
import pickle,gzip
import urllib.request
import numpy as np
import time
import tarfile
from tqdm import tqdm
import zipfile
from scipy.io.wavfile import read as wav_read
import io

def download(path):

    # Check if directory exists
    if not os.path.isdir(path+'audiomnist'):
        print('Creating audiomnist Directory')
        os.mkdir(path+'audiomnist')
    url = 'https://github.com/soerenab/AudioMNIST/archive/master.zip'
    # Check if file exists
    if not os.path.exists(path+'audiomnist/data.zip'):
        td  = time.time()
        urllib.request.urlretrieve(url, path+'audiomnist/data.zip')


def load(path=None, subsample=1):
    """Audio MNIST.

    https://github.com/soerenab/AudioMNIST


    Parameters
    ----------
        path: str (optional)
            default $DATASET_path), the path to look for the data and
            where the data will be downloaded if not present
    """

    if path is None:
        path = os.environ['DATASET_PATH']
    download(path)
    t0 = time.time()

    # load wavs
    f = zipfile.ZipFile(path+'audiomnist/data.zip')
    wavs = list()
    digits = list()
    speakers = list()
    N = 0
    for filename in f.namelist():
        if '.wav' not in filename:
            continue
        filename_end = filename.split('/')[-1]
        digits.append(int(filename_end.split('_')[0]))
        speakers.append(int(filename_end.split('_')[1])-1)
        wavfile   = f.read(filename)
        byt       = io.BytesIO(wavfile)
        wavs.append(wav_read(byt)[1].astype('float32')[::subsample])
        N = max(N, len(wavs[-1]))

    digits = np.array(digits)
    speakers = np.array(speakers)
    all_wavs = np.zeros((len(wavs), N))
    for i in range(len(wavs)):
        left = (N-len(wavs[i])) // 2
        all_wavs[i, left: left + len(wavs[i])] = wavs[i]
    return all_wavs, digits, speakers
