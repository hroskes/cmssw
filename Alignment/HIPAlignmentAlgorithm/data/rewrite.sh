#!/bin/bash
i=0
while read line
do
    name=$line
		let i=i+1
		if [ $(($i%50)) -eq 0 ]
			then
			#echo "\n">> ALCARECOTkAlCosmicsCTF0T.dat
			echo "'$name'" >> ALCARECOTkAlCosmicsCTF0T.dat 
		else
			echo "'$name'" | tr "\n" "," >> ALCARECOTkAlCosmicsCTF0T.dat 
		fi
		#if [ $i -eq 51 ]
		#	then break
		#fi
done < $1
