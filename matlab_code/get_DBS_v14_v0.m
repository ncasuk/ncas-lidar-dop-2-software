function [DBS]=get_DBS_v14_v0(fn)

%Parser for Processed Wind Profile files. 
%version v14 of Stream Line software
%version v0
%BJB June 2016
%input
%   fn: file name
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

%parse date
%find exenssion .
ix=strfind(fn,'.');

DBS.DT(1)=str2num(fn(ix(1)-15:ix(1)-12));
DBS.DT(2)=str2num(fn(ix(1)-11:ix(1)-10));
DBS.DT(3)=str2num(fn(ix(1)-9:ix(1)-8));
DBS.DT(4)=str2num(fn(ix(1)-6:ix(1)-5));
DBS.DT(5)=str2num(fn(ix(1)-4:ix(1)-3));
DBS.DT(6)=str2num(fn(ix(1)-2:ix(1)-1));
[DBS.DoY,DBS.ST,DBS.ET]=file_times(DBS.DT');
clear ix

%read in data
DBS.ng=dlmread(fn,'',[0 0 0 0]);
temp=dlmread(fn,'',1, 0);

%create arrays
DBS.ZZ=ones(1,DBS.ng).*(-1e+020);
DBS.FF=ones(1,DBS.ng).*(-1e+020);
DBS.DD=ones(1,DBS.ng).*(-1e+020);
DBS.flag=ones(1,DBS.ng);

%parse data
Z=temp(:,1);
DBS.ZZ(1:DBS.ng)=Z+(mean(diff(Z)))/2;
DBS.DD(1:DBS.ng)=temp(:,2);
DBS.FF(1:DBS.ng)=temp(:,3);
end

