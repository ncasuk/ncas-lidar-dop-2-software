function [D] = get_lidar_beta_v14_v0(fn)

%Parser for all lidar files other than DBS. 
%version v9 of Stream Line software
%version v0
%BJB June 2016
%input
%   fn: file name
%output
%   D: data structure
%           DT: date and time og profile
%           DoY: Day of tear
%           ST: serial time
%           EP: Epoch time
%           ZZ: range from instrument - mid point of measurement bin
%           BB: aerosol backscatter
%           WW: line of sight radial velocity
%           II: signal Intensity
%           SNR: signal to noise
%           ng: number of gates
%           flag: QC flag

%Parse header
fid=fopen(fn);
for n=1:50
    junk=fgetl(fid);
    if length(junk)>=15
        if (strcmp('Number of gates',junk(1:15))==1)
            ix=strfind(junk,':');
            ng=str2num(junk(ix(1)+1:end));
            clear ix
        end
    end
    if length(junk)>=17
        if (strcmp('Range gate length',junk(1:17))==1)
            ix=strfind(junk,':');
            gl=str2num(junk(ix(1)+1:end));
        end
    end
    if length(junk)>=32
        if (strcmp('Start time',junk(1:10))==1)
            ix=strfind(junk,':');
            yr=str2num(junk(ix(1)+1:ix(1)+5));
            mn=str2num(junk(ix(1)+6:ix(1)+7));
            dy=str2num(junk(ix(1)+8:ix(1)+9)); 
        end
    end
    if junk(1)=='*'
        start=n;
        break
    end
    clear junk    
end
fclose('all');

%read in data
temp=dlmread(fn,'',start, 0);

%sort data
%no of data blocks
ix=find(temp(:,1)==0);%look for gate 0

for n=1:length(ix)
    if n<length(ix)
        gate(n)=length(temp(ix(n)+1:(ix(n+1)-1),1));
    else
        gate(n)=length(temp(ix(n):(length(temp)),1));
    end
end

if max(gate)>ng
    ng=max(gate);
end
clear gate

% create arrays
D.DT=ones(length(ix),6);
D.DT(:,1)=D.DT(:,1).*yr;
D.DT(:,2)=D.DT(:,2).*mn;
D.DT(:,3)=D.DT(:,3).*dy;
D.DoY=ones(length(ix),1).*NaN;
D.ST=ones(length(ix),1).*NaN;
D.ET=ones(length(ix),1).*NaN;
D.AZ=ones(length(ix),1).*NaN;
D.PT=ones(length(ix),1).*NaN;%pitch
D.RO=ones(length(ix),1).*NaN;%role
D.EL=ones(length(ix),1).*NaN;
D.ZZ=ones(length(ix),ng).*NaN;
D.BB=ones(length(ix),ng).*NaN;
D.WW=ones(length(ix),ng).*NaN;
D.II=ones(length(ix),ng).*NaN;
D.SR=ones(length(ix),ng).*NaN;
D.flag=ones(length(ix),ng);
D.ng=ng;

% parse data
for n=1:length(ix)
    if n<length(ix)
        gate=temp(ix(n)+1:(ix(n+1)-1),1);
        hours=temp(ix(n)-1,1);
        xx=datevec(hours/24);
        D.DT(n,4:6)=xx(4:6);clear hours xx
        D.EL(n)=temp(ix(n)-1,3);
        D.AZ(n)=temp(ix(n)-1,2);
        D.PT(n)=temp(ix(n)-1,4);
        D.RO(n)=temp(ix(n)-1,5);
        D.WW(n,1:length(gate))=temp(ix(n)+1:(ix(n+1)-1),2);
        D.II(n,1:length(gate))=temp(ix(n)+1:(ix(n+1)-1),3);
        D.SR(n,1:length(gate))=D.II(n,1:length(gate))-1;
        D.BB(n,1:length(gate))=temp(ix(n)+1:(ix(n+1)-1),4);
        if length(gate)<=533
            D.ZZ(n,1:length(gate))=([0:(length(gate)-1)]+0.5).*gl;
        else
            D.ZZ(n,1:length(gate))=([0:(length(gate)-1)]+0.5).*3;
        end
    else
        gate=temp(ix(n):(length(temp)),1);
        hours=temp(ix(n)-1,1);
        xx=datevec(hours/24);
        D.DT(n,4:6)=xx(4:6);clear hours xx
        D.EL(n)=temp(ix(n)-1,3);
        D.AZ(n)=temp(ix(n)-1,2);
        D.PT(n)=temp(ix(n)-1,4);
        D.RO(n)=temp(ix(n)-1,5);
        D.WW(n,1:length(gate))=temp(ix(n):length(temp),2);
        D.II(n,1:length(gate))=temp(ix(n):length(temp),3);
        D.SR(n,1:length(gate))=D.II(n,1:length(gate))-1;
        D.BB(n,1:length(gate))=temp(ix(n):length(temp),4);
        if length(gate)<=533
            D.ZZ(n,1:length(gate))=([0:(length(gate)-1)]+0.5).*gl;
        else
            D.ZZ(n,1:length(gate))=([0:(length(gate)-1)]+0.5).*3;
        end
    end
end
clear ix
[DoY, ST, ET]=file_times(D.DT');D.DoY=DoY'; D.ST=ST'; D.ET=ET';


end

