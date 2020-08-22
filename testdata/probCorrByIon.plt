reset session
unset multiplot
set grid
set encoding utf8
f = 'probCorrByIon.dat'
set yrange [*<0:1<*]
set term wxt enhanced size 1024,768 noraise title 'Raman Probe (bright probability by ion plot, correction disabled)'
bind "shift-Button1" 'set label 10 "scanCenter" at MOUSE_X,MOUSE_Y rotate by 90 offset -2,1 front; set arrow 10 from MOUSE_X, MOUSE_Y+10 to MOUSE_X, MOUSE_Y lw 2 front; print "SHIFT_MOUSE_INPUT	",MOUSE_X,"	",MOUSE_Y; replot'
bind "x" 'print "INPUT x"'
bind "PageUp" 'print "INPUT PageUp"'
bind "PageDown" 'print "INPUT PageDown"'
unset arrow
unset label
set format "%.6g"
set mouse mouseformat "%.6g,%.6g"
set title "Shift-click to update scanCenter"
plot f u 1:5:6 w yerrorlines t 'GR4car ion 0 bright', \
f u 1:9:10 w yerrorlines t 'GR4car ion 1 bright'
