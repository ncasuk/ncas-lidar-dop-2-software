import parse
import numpy as np
import datetime as dt


def getStareFileHeader(input_file):
    #Pythonised, DW 2015-06-18
    with open(input_file, 'rt') as fid:
        m=1
        temp=fid.readline()
        while temp[0:4] != '****':
            #linelength=length_(temp)
            tempsplit = temp.split("\t")
            if tempsplit[0] == 'Start time:':
                datadate=tempsplit[1][0:8]
            if tempsplit[0] == 'Number of gates:':
                gate_number=int(tempsplit[1])
            if tempsplit[0] == 'Range gate length (m):':
                gate_length=float(tempsplit[1])
            if tempsplit[0] == 'Pulses/ray:':
                pulses_per_ray=float(tempsplit[1])
            if tempsplit[0] == 'No. of rays in file:':
                rays_per_point=float(tempsplit[1])
            if tempsplit[0] == 'Focus range:':
                focus_range=float(tempsplit[1])
            if tempsplit[0] == 'Resolution (m/s):':
                resolution=float(tempsplit[1])
            m=m + 1
            temp=fid.readline()

    headerlines_number=m
    return headerlines_number,gate_number,gate_length,datadate,pulses_per_ray,rays_per_point,focus_range,resolution



def getStareFileData(input_file, headerlines_number=None,gate_number=None):
    TimeStamp = []
    raw_data=[]
    #Pythonised, DW 2015-07-13
    with open(input_file, 'rt') as fid:
        formatTime=parse.compile('{:f} {:f} {:f}')
        formatSpec=parse.compile('{:d} {:f} {:f} {:e}')
        n=1
        for _ in range(headerlines_number):
            next(fid)

        #until end of file
        for timeline in fid:
            TimeStamp.append(formatTime.parse(timeline.strip().replace('  ',' ')))
            scan_data = np.empty([gate_number, 4])
            for i in range(gate_number):
                line = formatSpec.parse(next(fid).strip())
                scan_data[i] = line.fixed[0:4]
    
            raw_data.append(scan_data)
            n=n + 1
    
    return TimeStamp,raw_data



def stareCellToStruct(TimeStamp, raw_data, gate_number):
    maximum=len(TimeStamp) 
    DT=np.empty([maximum,1])
    AZ=np.empty([maximum,1])
    EL=np.empty([maximum,1])
    RG=np.empty([maximum,gate_number])
    D=np.empty([maximum,gate_number])
    I=np.empty([maximum,gate_number])
    B=np.empty([maximum,gate_number])
    for i in range(0,maximum):
        DT[i]=TimeStamp[i][0]
        AZ[i]=TimeStamp[i][1]
        EL[i]=TimeStamp[i][2]
        RG[i,:]=(raw_data[i][:,0])
        D[i,:]=(raw_data[i][:,1])
        I[i,:]=(raw_data[i][:,2])
        B[i,:]=(raw_data[i][:,3])
    return DT, AZ, EL, RG, D, I, B, maximum



def decTimetoDecDate(datadate, maximum, gate_number, DT):
    dt_init = dt.datetime.strptime(datadate, '%Y%m%d')
    Decimal_Year = datetime2matlabdn(dt_init)
    DD=np.empty([maximum,gate_number])
    DD.fill(np.nan)
    DP=np.empty(maximum, dtype=dt.datetime)#, dtype='datetime64[s]')
    #DP.fill(np.nan)
    hours_to_add = 0
    for i in range(0,maximum):
        if i > 0 and (DT[i,0] < DT[i-1,0]) and (DT[i,0] < 1):
            hours_to_add = 24
        #DP[i] = np.datetime64((dt_init + dt.timedelta(hours=DT[i,0])).strftime('%Y-%m-%dT%H:%M:%SZ'))
        DP[i] = (dt_init + dt.timedelta(hours=(DT[i,0]+hours_to_add)))#.strftime('%Y-%m-%dT%H:%M:%SZ')
        for m in range(0,gate_number):
            DD[i,m] = Decimal_Year + ((DT[i]+hours_to_add) / 24)
    return DD, DP


def datetime2matlabdn(dt_init):
    mdn = dt_init + dt.timedelta(days = 366)
    frac_seconds = (dt_init-dt.datetime(dt_init.year,dt_init.month,dt_init.day,0,0,0)).seconds / (24.0 * 60.0 * 60.0)
    frac_microseconds = dt_init.microsecond / (24.0 * 60.0 * 60.0 * 1000000.0)
    return mdn.toordinal() + frac_seconds + frac_microseconds



def gateRangeToAlt(RG, gate_length):
    A = (RG + 0.5) * gate_length
    return A



def readLidarFile(input_file):
    num_headerlines,gate_number,gate_length,datadate,pulses_per_ray,rays_per_point,focus_range,resolution = getStareFileHeader(input_file)
    TimeStamp, raw_data = getStareFileData(input_file, num_headerlines, gate_number)
    #print(num_headerlines)
    #print(gate_number)
    #print(gate_length)
    #print(datadate)
    #print(TimeStamp)
    #print(raw_data[0].shape)
    if len(raw_data) > 0:
        DT, AZ, EL, RG, D, I, B, maximum = stareCellToStruct(TimeStamp, raw_data, gate_number)
        DD, DP = decTimetoDecDate(datadate, maximum, gate_number, DT)
        A = gateRangeToAlt(RG, gate_length)
        #print(A)
    return {'num_headerlines': num_headerlines, 'gate_number': gate_number, 'gate_length': gate_length, 'datadate': datadate, 'TimeStamp': TimeStamp, 'DT': DT, 'AZ': AZ, 'EL': EL, 'RG': RG, 'D': D, 'I': I, 'B': B, 'maximum': maximum, 'DD': DD, 'DP': DP, 'A': A, 'pulses_per_ray': pulses_per_ray, 'rays_per_point': rays_per_point, 'focus_range': focus_range, 'resolution': resolution}
    

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    all_data = readLidarFile(input_file)
    print(all_data)
