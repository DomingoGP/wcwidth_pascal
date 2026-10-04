{ Pascal implementation of wcwidth function.

  Copyright (C) 2026 Domingo Galmés dgalmesp@gmail.com

  This library is free software; you can redistribute it and/or modify it
  under the terms of the GNU Library General Public License as published by
  the Free Software Foundation; either version 2 of the License, or (at your
  option) any later version with the following modification:

  As a special exception, the copyright holders of this library give you
  permission to link this library with independent modules to produce an
  executable, regardless of the license terms of these independent modules,and
  to copy and distribute the resulting executable under terms of your choice,
  provided that you also meet, for each linked independent module, the terms
  and conditions of the license of that module. An independent module is a
  module which is not derived from or based on this library. If you modify
  this library, you may extend this exception to your version of the library,
  but you are not obligated to do so. If you do not wish to do so, delete this
  exception statement from your version.

  This program is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
  FITNESS FOR A PARTICULAR PURPOSE. See the GNU Library General Public License
  for more details.

  You should have received a copy of the GNU Library General Public License
  along with this library; if not, write to the Free Software Foundation,
  Inc., 51 Franklin Street - Fifth Floor, Boston, MA 02110-1335, USA.
}


unit wcwidthu;

{$mode ObjFPC}{$H+}
{$R-}

interface

uses
  Classes, SysUtils;

function wcwidth(aCodePoint: uint32): integer;


implementation


{$I wcwidth.inc}

const

  LAST_CODEPOINT = $10FFFF;


function wcwidth(aCodePoint: uint32): integer;
var
  wp: Pdata;
  wPivot, wLeft, wRight: integer;
begin
  if aCodePoint = 0 then
    Exit(0);
  if (aCodePoint < 32) or (aCodePoint = 127) then
    Exit(-1);
  //first test most used chars
  wp := @table[0];
  if (aCodePoint < wp^.rs) then
    Exit(1);

  if aCodePoint > LAST_CODEPOINT then
    Exit(-1);

  wLeft := 0;
  wRight := High(table);

  if (aCodePoint > (table[wRight].rs + table[wRight].rl)) then
    Exit(1);
  //binary search.
  while wLeft <= wRight do
  begin
    wPivot := wLeft + ((wRight - wLeft) shr 1);
    wp := @table[wPivot];
    if (aCodePoint >= wp^.rs) and (aCodePoint <= (wp^.rs + wp^.rl)) then
      Exit(wp^.cw)
    else if wp^.rs < aCodePoint then
      wLeft := wPivot + 1
    else
      wRight := wPivot - 1;
  end;
  Result := 1;
end;

end.
