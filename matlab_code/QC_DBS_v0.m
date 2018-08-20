function [DBS]=QC_DBS_v0(DBS)

%QC for Processed Wind Profile files. 
%version v9 of Stream Line software
%version v0
%BJB June 2016
%input
%   DBS: data structure
%           DT: date and time og profile
%           DoY: Day of tear
%           ST: serial time
%           EP: Epoch time
%           ZZ: height above instrument - mid point of measurement bin
%           FF: wind speed
%           DD: wind direction
%           flag: QC flag
%           ng: no gates
%output
%   DBS: data structure
%           DT: date and time og profile
%           DoY: Day of tear
%           ST: serial time
%           EP: Epoch time
%           ZZ: height above instrument - mid point of measurement bin
%           FF: wind speed
%           DD: wind direction
%           flag: QC flag
%           ng: no gates

%flags
%   1 - data good
%   2 - data outside measurment range (greater set distance)
%   3 - FF > 20ms-1
%   4 - FF == 0
%   5 - shear >|5ms-1|
%   6 - time stamp error
%   7 - internal temperature < 15
%   8 - intenal temperature > 40

%flag 2
ix=find(isnan(DBS.ZZ)==1);
if ~isempty(ix)
    DBS.flag(ix)=2;
end

% flag 3
ix=find(DBS.FF>20);
if ~isempty(ix)
    DBS.flag(ix)=3;
end

%flag 4
ix=find(DBS.FF<=0);
if ~isempty(ix)
    DBS.flag(ix)=4;
end

%flag 5
ix1=find(diff(DBS.FF)>5);
ix2=find(diff(DBS.FF)<-5);
if ~isempty(ix1)
    DBS.flag(ix1)=5;
end
if ~isempty(ix2)
    DBS.flag(ix2)=5;
end

%flag 6, 7, & 8
%not something you can code for
%done by hand if needed

%replace NaNS
ix=find(isnan(DBS.ZZ));
if ~isempty(ix1)
    DBS.ZZ(ix)=-1e+20;
end
clear ix

ix=find(isnan(DBS.FF));
if ~isempty(ix)
    DBS.FF(ix)=-1e+20;
end
clear ix

ix=find(isnan(DBS.DD));
if ~isempty(ix)
    DBS.DD(ix)=-1e+20;
end
clear ix
end