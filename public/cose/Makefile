default:
	make claymore/claymore.html
	make zaffiro/zaffiro.html
	make simoun/simoun.html
	make ideon/ideon.html
	make sasurai/sasurai.html
	make mazinger/mazinger.html

claymore/claymore.html: claymore/claymore.txt
	python $S/accenti.py claymore/claymore.txt
	python $S/m2h.py claymore/claymore.txt

zaffiro/zaffiro.html: zaffiro/zaffiro.txt
	python $S/accenti.py zaffiro/zaffiro.txt
	python $S/m2h.py zaffiro/zaffiro.txt

simoun/simoun.html: simoun/simoun.txt
	python $S/accenti.py simoun/simoun.txt
	python $S/m2h.py simoun/simoun.txt

ideon/ideon.html: ideon/ideon.txt
	python $S/accenti.py ideon/ideon.txt
	python $S/m2h.py ideon/ideon.txt

sasurai/sasurai.html: sasurai/sasurai.txt
	python $S/accenti.py sasurai/sasurai.txt
	python $S/m2h.py sasurai/sasurai.txt

mazinger/mazinger.html: mazinger/mazinger.txt
	python $S/accenti.py mazinger/mazinger.txt
	python $S/m2h.py mazinger/mazinger.txt

## $S/md2ac.py is the script to extract a text suitable for AnimeClick
