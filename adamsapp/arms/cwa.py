from struct import *
import time
from datetime import datetime
from urllib.parse import unquote_plus
import io


def byte(value):
    return (value + 2 ** 7) % 2 ** 8 - 2 ** 7 


def ushort(value):
    return value % 2 ** 16


def short(value):
    return (value + 2 ** 15) % 2 ** 16 - 2 ** 15


class CWASample:
    pass


class CWA:
    def read(self, bytes):
        data = self.fh.read(bytes)
        if len(data) == bytes:
            return data
        else:
            raise IOError
    
    def __init__(self, filename):
        self.fh = open(filename, 'rb')

    def convert(self):
        try:
            header = self.read(2)
            unix_time = []
            gX = []
            gY = []
            gZ = []
            while len(header) == 2:
                if header == b'MD':
                    print('MD')
                    self.parse_header()
                elif header == b'UB':
                    print('UB')
                    blockSize = unpack('H', self.read(2))[0]
                elif header == b'SI':
                    print('SI')
                elif header == b'AX':
                    packetLength = unpack('H', self.read(2))[0]               
                    deviceId = unpack('H', self.read(2))[0]
                    sessionId = unpack('I', self.read(4))[0]
                    sequenceId = unpack('I', self.read(4))[0]
                    sampleTime = self.read_timestamp(self.read(4))
                    light = unpack('H', self.read(2))[0]
                    temperature = unpack('H', self.read(2))[0]
                    events = self.read(1)
                    battery = unpack('B', self.read(1))[0]
                    sampleRate = unpack('B', self.read(1))[0]
                    numAxesBPS = unpack('B', self.read(1))[0]
                    timestampOffset = unpack('h', self.read(2))[0]
                    sampleCount = unpack('H', self.read(2))[0]
                    
                    sampleData = io.BytesIO(self.read(480))
                    checksum = unpack('H', self.read(2))[0]
                    
                    if packetLength != 508:
                        continue
                    
                    if sampleTime == None:
                        continue
                    
                    if sampleRate == 0:
                        chksum = 0
                    else:
                        # rewind for checksum calculation
                        self.fh.seek(-packetLength - 4, 1)
                        # calculate checksum
                        chksum = 0
                        for x in range(int(packetLength / 2 + 2)):
                            chksum += unpack('H', self.read(2))[0]
                        chksum %= 2 ** 16
                    
                    if chksum != 0:
                        continue
                    
                    if sessionId != self.sessionId:
                        print("x")
                        continue
                    
                    if ((numAxesBPS >> 4) & 15) != 3:
                        print('[ERROR: num-axes not expected]')
                        
                    if (numAxesBPS & 15) == 2:
                        bps = 6
                    elif (numAxesBPS & 15) == 0:
                        bps = 4
                    
                    timestamp = time.mktime(sampleTime)
                    freq = 3200 / (1 << (15 - sampleRate & 15))
                    if freq <= 0:
                        freq = 1
                    offsetStart = float(-timestampOffset) / float(freq)
                    
                    time0 = float(timestamp) + offsetStart
                    
                    print("*")
                    for x in range(sampleCount):
                        sample = CWASample()
                        if bps == 6:
                            sample.x = unpack('h', sampleData.read(2))[0]
                            sample.y = unpack('h', sampleData.read(2))[0]
                            sample.z = unpack('h', sampleData.read(2))[0]
                        elif bps == 4:
                            temp = unpack('I', sampleData.read(4))[0]
                            temp2 = (6 - byte(temp >> 30))
                            sample.x = short(short((ushort(65472) & ushort(temp << 6))) >> temp2)
                            sample.y = short(short((ushort(65472) & ushort(temp >> 4))) >> temp2)
                            sample.z = short(short((ushort(65472) & ushort(temp >> 14))) >> temp2)
                        
                        sample.t = float(x) / float(freq) + time0

                        unix_time.append(sample.t)
                        gX.append(sample.x)
                        gY.append(sample.y)
                        gZ.append(sample.z)

                header = self.read(2)
        except IOError:
            pass

        return {'time': unix_time, 'gX': gX, 'gY': gY, 'gZ': gZ}
        
    def parse_header(self):
        blockSize = unpack('H', self.read(2))[0]
        performClear = unpack('B', self.read(1))[0]
        deviceId = unpack('H', self.read(2))[0]
        sessionId = unpack('I', self.read(4))[0]
        shippingMinLightLevel = unpack('H', self.read(2))[0]
        loggingStartTime = self.read(4)
        loggingEndTime = self.read(4)
        loggingCapacity = unpack('I', self.read(4))[0]
        allowStandby = unpack('B', self.read(1))[0]
        debuggingInfo = unpack('B', self.read(1))[0]
        batteryMinimumToLog = unpack('H', self.read(2))[0]
        batteryWarning = unpack('H', self.read(2))[0]
        enableSerial = unpack('B', self.read(1))[0]
        lastClearTime = self.read(4)
        samplingRate = unpack('B', self.read(1))[0]
        lastChangeTime = self.read(4)
        firmwareVersion = unpack('B', self.read(1))[0]

        reserved = self.read(22)

        annotationBlock = self.read(448 + 512)
        
        if len(annotationBlock) < 448 + 512:
            annotationBlock = ""

        annotation = ""
        for x in str(annotationBlock):
            if ord(x) != 255 and x != ' ':
                if x == '?':
                    x = '&'
                annotation += x
        annotation = annotation.strip()

        annotationElements = annotation.split('&')
        annotationNames = {
                # at device set-up time
                '_c': 'studyCentre',
                '_s': 'studyCode',
                '_i': 'investigator',
                '_x': 'exerciseCode',
                '_v': 'volunteerNum',
                '_p': 'bodyLocation',
                '_so': 'setupOperator',
                '_n': 'notes',
                # at retrieval time
                '_b': 'startTime', 
                '_e': 'endTime', 
                '_ro': 'recoveryOperator', 
                '_r': 'retrievalTime', 
                '_co': 'comments'}
        annotations = dict()
        for element in annotationElements:
            kv = element.split('=', 2)
            if kv[0] in annotationNames:
                annotations[annotationNames[kv[0]]] = unquote_plus(kv[1])

        for x in ('startTime', 'endTime', 'retrievalTime'):
            if x in annotations:
                if '/' in annotations[x]:
                    annotations[x] = time.strptime(annotations[x], '%d/%m/%Y')
                else:
                    annotations[x] = time.strptime(annotations[x], '%Y-%m-%d %H:%M:%S')

        self.annotations = annotations
        self.deviceId = deviceId
        self.sessionId = sessionId
        self.lastClearTime = self.read_timestamp(lastClearTime)
        self.lastChangeTime = self.read_timestamp(lastChangeTime)
        self.firmwareVersion = firmwareVersion if firmwareVersion != 255 else 0


    def read_timestamp(self, stamp):
        stamp = unpack('I', stamp)[0]
        # bit pattern:  YYYYYYMM MMDDDDDh hhhhmmmm mmssssss
        year  = ((stamp >> 26) & 0x3f) + 2000
        month = (stamp >> 22) & 0x0f
        day   = (stamp >> 17) & 0x1f
        hours = (stamp >> 12) & 0x1f
        mins  = (stamp >>  6) & 0x3f
        secs  = (stamp >>  0) & 0x3f
        try:
            t = time.strptime(str(datetime(year, month, day, hours, mins, secs)), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            t = None
        return t


def main():
    filename = 'test.cwa'
    data_array = CWA(filename)


if __name__ == "__main__":
    main()
