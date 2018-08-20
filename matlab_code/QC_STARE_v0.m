function [D]=QC_STARE_v0(D)

%QC for non WP files. 
%version v9 of Stream Line software
%version v0
%BJB June 2016
%input
%   D: data structure
%           DT: date and time og profile
%           DoY: Day of tear
%           ST: serial time
%           EP: Epoch time
%           AZ: Azimuth angle
%           EL: Elevation angle
%           ZZ: range from instrument - mid point of measurement bin
%           BB: aerosol backscatter
%           WW: line of sight radial velocity
%           II: signal Intensity
%           SNR: signal to noise
%           flag: QC flag
%output
%   D: data structure
%           DT: date and time og profile
%           DoY: Day of tear
%           ST: serial time
%           EP: Epoch time
%           AZ: Azimuth angle
%           EL: Elevation angle
%           ZZ: range from instrument - mid point of measurement bin
%           BB: aerosol backscatter
%           WW: line of sight radial velocity
%           II: signal Intensity
%           SNR: signal to noise
%           flag: QC flag

%flags
%   1 - data good
%   2 - data outside measurment range (greater set distance)
%   3 - Signal below instrument threshold
%   4 - LoS > |19m\s|
%   5 - LoS shear >|5ms-1|
%   6 - time stamp error
%   7 - internal temperature < 15
%   8 - intenal temperature > 40

%Packing NaNs
ix=find(isnan(D.ZZ));
if ~isempty(ix)
    D.flag(ix)=D.flag(ix).*NaN;
end
clear ix

%flag 1
ix=find(isnan(D.ZZ)>9000);
if ~isempty(ix)
    D.flag(ix)=2;
end
clear ix

%flag 2
[d,r]=size(D.BB);
for n=1:d
     % varying threshold
    ix=find((D.II(n,:)>1)&(D.II(n,:)<1.015));
    threshold=mean(D.II(n,ix))+(1.5*std(D.II(n,ix)));
    clear ix
    
    ix=find(D.II(n,:)<threshold);
    if ~isempty(ix)
        D.flag(n,ix)=3;
    end
    clear ix
    
    %deal with background breakthrough
    if (mean(D.BB(n,r-20:r-1))>0)
        temp=D.BB(n,:);
        ix=find(temp<0);
        X=ix(end):r-2;Y=log10(temp(ix(end):r-2));
        [p,f]=polyfit(X,Y,2);
        xx=ix(end):r;yy=10.^polyval(p,xx);   
        y1=zeros(1,r);y1(1,ix(end):r)=yy;
        clear ix
        
        ixx=find(temp<(y1.*1.2));
        if ~isempty(ixx)
            D.flag(n,ixx)=3;
        end
        clear ixx y1 xx yy p f X Y ix temp
    end
    
    % BB range
    ix=find(D.BB(n,:)<=1e-7);
    if ~isempty(ix)
        D.flag(n,ix)=3;
    end
    clear ix
    
    ix=find(D.BB(n,:)>1e-3);
    if ~isempty(ix)
        D.flag(n,ix)=3;
    end
    clear ix
end
clear d r

%flag 4
ix1=find(D.WW>19);
ix2=find(D.WW<-19);
if ~isempty(ix1)
    D.flag(ix1)=4;
end
if ~isempty(ix2)
    D.flag(ix2)=4;
end
clear ix1 ix2

%flag 5
[d,r]=size(D.WW);
for n=1:d
    temp=diff(D.WW(n,:));
    
    ix1=find(temp>5);
    ix2=find(temp<-5);
    if ~isempty(ix1)
        D.flag(n,ix1)=5;
    end
    clear ix1
    if ~isempty(ix2)
        D.flag(n,ix2)=5;
    end
    clear ix2
end
clear d r

%flag 6
ix=find(diff(D.DoY)<0);
if ~isempty(ix)
    D.flag(ix+1,:)=6;
end

%flag 7, & 8
%not something you can code for
%done by hand if needed


%replace NaNS
ix=find(isnan(D.ZZ));
if ~isempty(ix)
    D.ZZ(ix)=-1e+20;
end
clear ix

ix=find(isnan(D.BB));
if ~isempty(ix)
    D.BB(ix)=-1e+20;
end
clear ix

ix=find(isnan(D.WW));
if ~isempty(ix)
    D.WW(ix)=-1e+20;
end
clear ix

ix=find(isnan(D.II));
if ~isempty(ix)
    D.II(ix)=-1e+20;
end
clear ix

ix=find(isnan(D.SR));
if ~isempty(ix)
    D.SR(ix)=-1e+20;
end
clear ix

ix=find(D.AZ<0);
if ~isempty(ix)
    D.AZ(ix)=0;
end
clear ix

ix=find(D.EL<0);
if ~isempty(ix)
    D.EL(ix)=0;
end
clear ix

end