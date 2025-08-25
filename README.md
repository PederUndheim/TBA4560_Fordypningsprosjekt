Heihei

----- info fra Håvard -----

Hei,

Her er litt info om filene.

dem.tif = Digital Elevation Model (10m)
pra_raw.tif = Potential Release Areas (PRA). Raw betyr at dette er rådata fra PRA-modellen og går fra 0 til 100, der 100 er mest sannsynlig løsneområdet, 0 er ikke løsneområdet, 1 er lite sannsynlig.
pra_binary.tif = Denne er binary (Løsneområder er 1, alt annet er 0). Denne er laget fra pra_raw.tif med en terskelverdi på 15 (alt over 15 = 1)
number_of_stems_ha.tif = skogdata som er brukt inn i Flow-Py (utløpsmodellering). Den viser antall stammer/ha med en stammediameter på mer enn 10 cm ved brysthøyde.
windshelter.tif = Dette er en proxy for kurvaturen i terrenget. Positive verdier er forsenkninger der snøen vil legge seg, mens negative verdier er oppstikkende terreng som rygger.

Flow-Py (utløpsmodell)
FP_travel_angle.tif = Modellerte utløpsområder fra pra_binary.tif til definerte alfavinkler. Det er vinkelen fra løsneområdet til et gitt punkt. Laveste verdi er 23 grader. (Lavere verdi = lenger utløp).
FP_travel_distance = Modellerte utløpsområder fra pra_binary.tif, men her er det avstand i meter fra løsneområdene.
FP_z_delta = En form for potensiell hastighet (kinetisk energi i skredet).

---

-- Users manual --
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
