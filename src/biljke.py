import enum


class Biljka(enum.Enum):
    PITOMI_KESTEN = "Pitomi kesten (Castanea sativa)"
    KOPRIVE = "Koprive (Urticaceae)"
    BOR = "Bor (Pinus sp.)"
    TRAVE = "Trave (Poaceae)"
    LIPA = "Lipa (Tilia sp.)"
    TRPUTAC = "Trputac (Plantago sp.)"
    MASLINA = "Maslina (Olea sp.)"
    HRAST_CRNIKA = "Hrast crnika (Quercus ilex)"
    CRKVINA = "Crkvina (Parietaria sp.)"
    CEMPRESI = "Čempresi (Cupressaceae)"
    AMBROZIJA = "Ambrozija (Ambrosia sp.)"
    HRAST = "Hrast (Quercus ilex)"
    LOBODA = "Loboda (Chenopodiaceae)"
    HRAST_SP = "Hrast (Quercus sp.)"
    PELIN = "Pelin (Artemisia sp.)"
    BRIJEST = "Brijest (Ulmus sp.)"
    JASEN = "Jasen (Fraxinus sp.)"
    JOHA = "Joha (Alnus sp.)"
    LIJESKA = "Lijeska (Corylus sp.)"
    TOPOLA = "Topola (Populus sp.)"
    VRBA = "Vrba (Salix sp.)"
    GRAB = "Grab (Carpinus sp.)"
    KISELICA = "Kiselica (Rumex sp.)"
    BREZA = "Breza (Betula sp.)"
    PLATANA = "Platana (Platanus sp.)"
    ORAH = "Orah (Juglans sp.)"

# Reverse lookup dictionary to map value to name
BILJKA_LOOKUP = {member.value: member.name for member in Biljka}