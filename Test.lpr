program Test;

uses sysutils, wcwidthu;

var
  i:integer;

procedure Check(aCodepoint:Uint32;aExpected:integer);
var
  wr:integer;
begin
  wr:=wcwidth(aCodePoint);
  writeln('[$',IntToHex(aCodepoint,8):3,' - ',wr:2,'] ');
  if wr<>aExpected then
    writeln('ERROR, expected ',aExpected);
end;

begin

  for i:=0 to 255 do
  begin
    if (i mod 10) =0 then
      writeln;
    write('[',i:3,' - ',wcwidth(i):2,'] ');
  end;
  writeln;

  Check($299,1);
  Check($300,0);
  Check($36F,0);
  Check($361,0);
  Check($36F,0);

  Check($482,1);
  Check($483,0);
  Check($1101,2);
  Check($1102,2);


  Check($0001D300,2);
  Check($0001D300-1,1);
  Check($0001D305,2);

  Check($000E01EF,0);
  Check($000E01F0,1);
  Check($000F01F0,1);
  Check($10FFFF,1);
  Check($10FFFF+1,-1);
  //some emojis
  Check($1F915,2);
  Check($1F479,2);
  Check($1F44D,2);


  writeln('Press enter to exit');
  readln;
end.

