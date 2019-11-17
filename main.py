import sys
import time
import pyaudio
import threading
import numpy as np
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QGridLayout, QLCDNumber
from PyQt5.QtGui import QKeySequence


class AudioManager():
    def __init__(self, rate=44100, n_chunk=1024):
        self.rate = rate
        self.n_chunk = n_chunk
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=rate, output=1,
                                  frames_per_buffer=n_chunk)

    def __render(self, freq, duration, offset=0, gain=0.4):
        pi2_t0 = 2 * np.pi / (self.rate / freq)
        N = (self.rate * duration) // self.n_chunk
        while self.stream.is_active() and N > 0:
            x =  np.arange(offset, offset + self.n_chunk)
            chunk = gain * np.sin(pi2_t0 * x)
            self.stream.write(chunk.astype(np.float32).tostring())
            offset += self.n_chunk
            N -= 1
        return True
        
    def sound(self, freq=440, duration=0.1):
        t = threading.Thread(target=self.__render, args=(freq, duration))
        t.start()
    
class BPM():
    def __init__(self, alpha=0.8):
        self.diff_pre = 0.5
        self.time_pre = 0.0
        self.counter = 0
        self.alpha = alpha
        self.n_buff = 8
        
    def __reset(self):
        self.counter = 0
        self.diff_pre = 0.5
        return 120
        
    def __calc(self):
        time_cur = time.time()
        if self.counter > 0:
            diff = time_cur - self.time_pre
            if diff > 3.0:
                bpm = self.__reset()
            else:
                if diff > 1.0:
                    diff = 1.0
                elif diff < 0.20:
                    diff = 0.20
                diff = self.alpha * diff  + \
                       (1.0 - self.alpha) * self.diff_pre
                bpm = 60 / diff
                self.diff_pre = diff
        else:
            bpm = self.__reset()
            
        self.time_pre = time_cur
        return bpm
        
    def count(self):
        counter = self.counter
        bpm = self.__calc()
        
        idx = counter % self.n_buff
        if counter == 0:
            self.bpms = np.array([bpm for k in range(self.n_buff)])
        else:
            self.bpms[idx] = bpm
        bpm_mean = int(np.mean(self.bpms)*10)//10
       
        self.counter += 1
        return bpm_mean, counter
        
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.bpm = BPM()
        self.am = AudioManager()
        self.bpm_list = None
        self.Init_UI()
        self.show()
        

    def Init_UI(self):
        self.setGeometry(100, 100, 250, 250)
        self.setWindowTitle('BPM Tap')
        
        grid = QGridLayout()
        self.lcd = QLCDNumber()
        grid.addWidget(self.lcd, 0, 0)
        
        grid.setSpacing(10)
       
        button = QPushButton("tap")
        grid.addWidget(button, 1, 0)
        button.clicked.connect(self.buttonClicked)
        self.setLayout(grid)

    def buttonClicked(self):
        bpm, count = self.bpm.count()
        c = count % 4 
        if count == 0:
             self.bpm_list = [0, 0, 0, 0]
        self.bpm_list[c] = bpm
            
        freq = 880 if c==0 else 440
        self.am.sound(freq=freq)
         
        print(f"{c+1}/4  Tap: {bpm}")
        self.lcd.display(f'{bpm}')
       
    def keyPressEvent(self, event):
        key = QKeySequence(event.key()).toString()
        self.buttonClicked()
        print(f"\tInput key: {key}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyWidget()
    app.exit(app.exec_())
