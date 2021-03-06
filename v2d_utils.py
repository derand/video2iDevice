#!/usr/bin/env python
# -*- coding: utf-8 -*-

# writed by derand

import sys
import os
import re

if sys.platform == 'darwin':
	script_dir = os.path.dirname(os.path.realpath(__file__))
	ffmpeg_path = script_dir + '/binary/ffmpeg'
	mp4box_path = script_dir + '/binary/MP4Box'
	AtomicParsley_path = script_dir + '/binary/AtomicParsley'
	mkvtoolnix_path = script_dir + '/binary/mkvtoolnix/'
	mediainfo_path = script_dir + '/binary/mediainfo'
else:
	ffmpeg_path = 'ffmpeg'
	mp4box_path = 'MP4Box'
	AtomicParsley_path = 'AtomicParsley'
	mkvtoolnix_path = ''
	mediainfo_path = 'mediainfo'


def add_separator_to_filepath(filepath):
	return re.escape(filepath)
	#for c in '\\ ()[]&":\'`':
	#	filepath = filepath.replace(c, '\\%s'%c)
	#return filepath



def video_size_convert(real1, real2, out1):
	out2 = (real2*out1)/real1
	if out2%16>7:
		out2 += 16-out2%16
	else:
		out2 -= out2%16
	return (out1, out2)



#source table http://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
LANGUAGES_DICT = { 
"Abkhazian":             "abk",
"Acehnese":              "ace",
"Achinese":              "ace",
"Acoli":                 "ach",
"Adangme":               "ada",
"Adygei":                "ady",
"Adyghe":                "ady",
"Afar":                  "aar",
"Afrihili":              "afh",
"Afrikaans":             "afr",
"Afroasiatic languages": "afa",
"Ainu":                  "ain",
"Akan":                  "aka",
"Akkadian":              "akk",
"Albanian":              "alb",
"Alemannic":             "gsw",
"Aleut":                 "ale",
"Algonquian languages":  "alg",
"Alsatian":              "gsw",
"Altaic languages":      "tut",
"Amharic":               "amh",
"Ancient Greek":         "grc",
"Angika":                "anp",
"Apache languages":      "apa",
"Arabic":                "ara",
"Aragonese":             "arg",
"Arapaho":               "arp",
"Arawak":                "arw",
"Armenian":              "arm",
"Aromanian":             "rup",
"Artificial languages":  "art",
"Arumanian":             "rup",
"Assamese":              "asm",
"Asturian":              "ast",
"Asturleonese":          "ast",
"Athabaskan languages":  "ath",
"Australian languages":  "aus",
"Austronesian languages":"map",
"Avaric":                "ava",
"Avestan":               "ave",
"Awadhi":                "awa",
"Aymara":                "aym",
"Azerbaijani":           "aze",
"Bable":                 "ast",
"Balinese":              "ban",
"Baltic languages":      "bat",
"Baluchi":               "bal",
"Bambara":               "bam",
"Bamileke languages":    "bai",
"Banda languages":       "bad",
"Bantu languages":       "bnt",
"Basa":                  "bas",
"Bashkir":               "bak",
"Basque":                "baq",
"Batak languages":       "btk",
"Bedawiyet":             "bej",
"Beja":                  "bej",
"Belarusian":            "bel",
"Bemba":                 "bem",
"Bengali":               "ben",
"Berber languages":      "ber",
"Bhojpuri":              "bho",
"Bihari languages":      "bih",
"Bikol":                 "bik",
"Bilin":                 "byn",
"Bini":                  "bin",
"Bislama":               "bis",
"Blackfoot":             "bla",
"Blin":                  "byn",
"Bliss":                 "zbl",
"Blissymbolics":         "zbl",
"Blissymbols":           "zbl",
"Bosnian":               "bos",
"Braj":                  "bra",
"Breton":                "bre",
"Buginese":              "bug",
"Bulgarian":             "bul",
"Buriat":                "bua",
"Burmese":               "bur",
"Caddo":                 "cad",
"Castilian":             "spa",
"Catalan":               "cat",
"Caucasian languages":   "cau",
"Cebuano":               "ceb",
"Celtic languages":      "cel",
"Central American Indian languages":"cai",
"Central Khmer":         "khm",
"Chagatai":              "chg",
"Chamic languages":      "cmc",
"Chamorro":              "cha",
"Chechen":               "che",
"Cherokee":              "chr",
"Chewa":                 "nya",
"Cheyenne":              "chy",
"Chibcha":               "chb",
"Chichewa":              "nya",
"Chinese":               "chi",
"Chinook Jargon":        "chn",
"Chipewyan":             "chp",
"Choctaw":               "cho",
"Chuang":                "zha",
"Church Slavic":         "chu",
"Church Slavonic":       "chu",
"Chuukese":              "chk",
"Chuvash":               "chv",
"Circassian":            "kbd",
"Classical Nepal Bhasa": "nwc",
"Classical Newari":      "nwc",
"Classical Syriac":      "syc",
"Cook Islands Maori":    "rar",
"Coptic":                "cop",
"Cornish":               "cor",
"Corsican":              "cos",
"Cree":                  "cre",
"Creek":                 "mus",
"Crimean Tatar":         "crh",
"Crimean Turkish":       "crh",
"Croatian":              "hrv",
"Cushitic languages":    "cus",
"Czech":                 "cze",
"Dakota":                "dak",
"Danish":                "dan",
"Dargwa":                "dar",
"Delaware":              "del",
"Dene Suline":           "chp",
"Dhivehi":               "div",
"Dimili":                "zza",
"Dimli":                 "zza",
"Dinka":                 "din",
"Divehi":                "div",
"Dogri":                 "doi",
"Dogrib":                "dgr",
"Dravidian languages":   "dra",
"Duala":                 "dua",
"Dutch":                 "dut",
"Dyula":                 "dyu",
"Dzongkha":              "dzo",
"Eastern Frisian":       "frs",
"Edo":                   "bin",
"Efik":                  "efi",
"Egyptian":              "egy",
"Ekajuk":                "eka",
"Elamite":               "elx",
"English":               "eng",
"Erzya":                 "myv",
"Esperanto":             "epo",
"Estonian":              "est",
"Ewe":                   "ewe",
"Ewondo":                "ewo",
"Fang":                  "fan",
"Fanti":                 "fat",
"Faroese":               "fao",
"Fijian":                "fij",
"Filipino":              "fil",
"Finnish":               "fin",
"Finno-Ugric languages": "fiu",
"Flemish":               "dut",
"Fon":                   "fon",
"French":                "fre",
"Friulian":              "fur",
"Fulah":                 "ful",
"Ga":                    "gaa",
"Gaelic":                "gla",
"Galibi Carib":          "car",
"Galician":              "glg",
"Ganda":                 "lug",
"Gayo":                  "gay",
"Gbaya":                 "gba",
"Ge'ez":                 "gez",
"Georgian":              "geo",
"German":                "ger",
"Germanic languages":    "gem",
"Gikuyu":                "kik",
"Gilbertese":            "gil",
"Gondi":                 "gon",
"Gorontalo":             "gor",
"Gothic":                "got",
"Grebo":                 "grb",
"Greenlandic":           "kal",
"Guarani":               "grn",
"Gujarati":              "guj",
"Gwich'in":              "gwi",
"Haida":                 "hai",
"Haitian":               "hat",
"Haitian Creole":        "hat",
"Hausa":                 "hau",
"Hawaiian":              "haw",
"Hebrew":                "heb",
"Herero":                "her",
"Hiligaynon":            "hil",
"Himachali languages":   "him",
"Hindi":                 "hin",
"Hiri Motu":             "hmo",
"Hittite":               "hit",
"Hmong":                 "hmn",
"Hungarian":             "hun",
"Hupa":                  "hup",
"Iban":                  "iba",
"Icelandic":             "ice",
"Ido":                   "ido",
"Igbo":                  "ibo",
"Ijo languages":         "ijo",
"Iloko":                 "ilo",
"Imperial Aramaic":      "arc",
"Inari Sami":            "smn",
"Indic languages":       "inc",
"Indo-European languages":"ine",
"Indonesian":            "ind",
"Ingush":                "inh",
"Interlingua":           "ina",
"Interlingue":           "ile",
"Inuktitut":             "iku",
"Inupiaq":               "ipk",
"Iranian languages":     "ira",
"Irish":                 "gle",
"Iroquoian languages":   "iro",
"Italian":               "ita",
"Japanese":              "jpn",
"Javanese":              "jav",
"Jingpho":               "kac",
"Judeo-Arabic":          "jrb",
"Judæo-Persian":        "jpr",
"Kabyle":                "kab",
"Kachin":                "kac",
"Kalaallisut":           "kal",
"Kalmyk":                "xal",
"Kamba":                 "kam",
"Kannada":               "kan",
"Kanuri":                "kau",
"Kapampangan":           "pam",
"Kara-Kalpak":           "kaa",
"Karachay-Balkar":       "krc",
"Karelian":              "krl",
"Karen languages":       "kar",
"Kashmiri":              "kas",
"Kashubian":             "csb",
"Kawi":                  "kaw",
"Kazakh":                "kaz",
"Khasi":                 "kha",
"Khoisan languages":     "khi",
"Khotanese":             "kho",
"Kikuyu":                "kik",
"Kimbundu":              "kmb",
"Kinyarwanda":           "kin",
"Kirdki":                "zza",
"Kirghiz":               "kir",
"Kiribati":              "gil",
"Kirmanjki":             "zza",
"Klingon":               "tlh",
"Komi":                  "kom",
"Kongo":                 "kon",
"Konkani":               "kok",
"Korean":                "kor",
"Kosraean":              "kos",
"Kpelle":                "kpe",
"Kru languages":         "kro",
"Kuanyama":              "kua",
"Kumyk":                 "kum",
"Kurdish":               "kur",
"Kurukh":                "kru",
"Kutenai":               "kut",
"Kwanyama":              "kua",
"Kyrgyz":                "kir",
"Ladino":                "lad",
"Lahnda":                "lah",
"Lamba":                 "lam",
"Land Dayak languages":  "day",
"Lao":                   "lao",
"Latin":                 "lat",
"Latvian":               "lav",
"Leonese":               "ast",
"Letzeburgesch":         "ltz",
"Lezghian":              "lez",
"Limburgan":             "lim",
"Limburger":             "lim",
"Limburgish":            "lim",
"Lingala":               "lin",
"Lithuanian":            "lit",
"Lojban":                "jbo",
"Low German":            "nds",
"Low Saxon":             "nds",
"Lower Sorbian":         "dsb",
"Lozi":                  "loz",
"Luba-Katanga":          "lub",
"Luba-Lulua":            "lua",
"Luiseño":              "lui",
"Lule Sami":             "smj",
"Lunda":                 "lun",
"Luo":                   "luo",
"Lushai":                "lus",
"Luxembourgish":         "ltz",
"Maasai":                "mas",
"Macedo-Romanian":       "rup",
"Macedonian":            "mkd",
"Madurese":              "mad",
"Magahi":                "mag",
"Maithili":              "mai",
"Makasar":               "mak",
"Malagasy":              "mlg",
"Malay":                 "may",
"Malayalam":             "mal",
"Maldivian":             "div",
"Maltese":               "mlt",
"Manchu":                "mnc",
"Mandar":                "mdr",
"Mandingo":              "man",
"Manipuri":              "mni",
"Manobo languages":      "mno",
"Manx":                  "glv",
"Mapuche":               "arn",
"Mapudungun":            "arn",
"Marathi":               "mar",
"Mari":                  "chm",
"Marshallese":           "mah",
"Marwari":               "mwr",
"Mayan languages":       "myn",
"Mende":                 "men",
"Mi'kmaq":               "mic",
"Micmac":                "mic",
"Middle":                "dum",
"Middle English":        "enm",
"Middle French":         "frm",
"Middle High German":    "gmh",
"Middle Irish":          "mga",
"Minangkabau":           "min",
"Mirandese":             "mwl",
"Modern Greek":          "gre",
"Mohawk":                "moh",
"Moksha":                "mdf",
"Mon-Khmer languages":   "mkh",
"Mongo":                 "lol",
"Mongolian":             "mon",
"Mossi":                 "mos",
"Multiple languages":    "mul",
"Munda languages":       "mun",
"Māori":                "mao",
"N'Ko":                  "nqo",
"Nahuatl":               "nah",
"Nauruan":               "nau",
"Navaho":                "nav",
"Navajo":                "nav",
"Ndonga":                "ndo",
"Neapolitan":            "nap",
"Nepal Bhasa":           "new",
"Nepali":                "nep",
"Newari":                "new",
"Nias":                  "nia",
"Niger-Congo languages": "nic",
"Nilo-Saharan languages":"ssa",
"Niuean":                "niu",
"Nogai":                 "nog",
"North American Indian languages":"nai",
"Northern Frisian":      "frr",
"Northern Ndebele":      "nde",
"Northern Sami":         "sme",
"Northern Sotho":        "nso",
"Norwegian":             "nor",
"Norwegian Bokmal":      "nob",
"Norwegian Nynorsk":     "nno",
"Nubian languages":      "nub",
"Nuosu":                 "iii",
"Nyamwezi":              "nym",
"Nyanja":                "nya",
"Nyankole":              "nyn",
"Nyoro":                 "nyo",
"Nzima":                 "nzi",
"Occidental":            "ile",
"Occitan":               "oci",
"Official Aramaic":      "arc",
"Oirat":                 "xal",
"Ojibwa":                "oji",
"Old Bulgarian":         "chu",
"Old Church Slavonic":   "chu",
"Old English":           "ang",
"Old French":            "fro",
"Old High German":       "goh",
"Old Irish":             "sga",
"Old Newari":            "nwc",
"Old Norse":             "non",
"Old Occitan":           "pro",
"Old Persian":           "peo",
"Old Provencal":         "pro",
"Old Slavonic":          "chu",
"Oriya":                 "ori",
"Oromo":                 "orm",
"Osage":                 "osa",
"Ossetian":              "oss",
"Ossetic":               "oss",
"Otomian languages":     "oto",
"Ottoman":               "ota",
"Pahlavi":               "pal",
"Palauan":               "pau",
"Pali":                  "pli",
"Pampanga":              "pam",
"Pangasinan":            "pag",
"Panjabi":               "pan",
"Papiamento":            "pap",
"Papuan languages":      "paa",
"Pashto":                "pus",
"Pashto language":       "pus",
"Pedi":                  "nso",
"Persian":               "per",
"Philippine languages":  "phi",
"Phoenician":            "phn",
"Pilipino":              "fil",
"Pohnpeian":             "pon",
"Polish":                "pol",
"Portuguese":            "por",
"Prakrit":               "pra",
"Punjabi":               "pan",
"Quechua":               "que",
"Rajasthani":            "raj",
"Rapanui":               "rap",
"Rarotongan":            "rar",
"Romance languages":     "roa",
"Romanian":              "rum",
"Romansh":               "roh",
"Romany":                "rom",
"Rundi":                 "run",
"Russian":               "rus",
"Sakan":                 "kho",
"Salishan languages":    "sal",
"Samaritan Aramaic":     "sam",
"Sami languages":        "smi",
"Samoan":                "smo",
"Sandawe":               "sad",
"Sango":                 "sag",
"Sanskrit":              "san",
"Santali":               "sat",
"Sardinian":             "srd",
"Sasak":                 "sas",
"Scots":                 "sco",
"Scottish Gaelic":       "gla",
"Selkup":                "sel",
"Semitic languages":     "sem",
"Sepedi":                "nso",
"Serbian":               "srp",
"Serer":                 "srr",
"Shan":                  "shn",
"Shona":                 "sna",
"Sichuan Yi":            "iii",
"Sicilian":              "scn",
"Sidamo":                "sid",
"Sign languages":        "sgn",
"Siksika":               "bla",
"Sindhi":                "snd",
"Sinhala":               "sin",
"Sinhalese":             "sin",
"Sino-Tibetan languages":"sit",
"Siouan languages":      "sio",
"Skolt Sami":            "sms",
"Slave":                 "den",
"Slavic languages":      "sla",
"Slovak":                "slk",
"Slovenian":             "slv",
"Sogdian":               "sog",
"Somali":                "som",
"Songhay languages":     "son",
"Soninke":               "snk",
"Sorbian languages":     "wen",
"South American Indian languages":"sai",
"Southern Altai":        "alt",
"Southern Ndebele":      "nbl",
"Southern Sami":         "sma",
"Southern Sotho":        "sot",
"Spanish":               "spa",
"Sranan Tongo":          "srn",
"Sukuma":                "suk",
"Sumerian":              "sux",
"Sundanese":             "sun",
"Susu":                  "sus",
"Swahili":               "swa",
"Swati":                 "ssw",
"Swedish":               "swe",
"Swiss German":          "gsw",
"Syriac":                "syr",
"Tagalog":               "tgl",
"Tahitian":              "tah",
"Tai languages":         "tai",
"Tajik":                 "tgk",
"Tamashek":              "tmh",
"Tamil":                 "tam",
"Tatar":                 "tat",
"Telugu":                "tel",
"Tereno":                "ter",
"Tetum":                 "tet",
"Thai":                  "tha",
"Tibetan":               "bod",
"Tigre":                 "tig",
"Tigrinya":              "tir",
"Time":                  "tem",
"Tiv":                   "tiv",
"Tlingit":               "tli",
"Tok Pisin":             "tpi",
"Tokelau":               "tkl",
"Tonga":                 "tog",
"Tsimshian":             "tsi",
"Tsonga":                "tso",
"Tswana":                "tsn",
"Tumbuka":               "tum",
"Tupian languages":      "tup",
"Turkish":               "tur",
"Turkmen":               "tuk",
"Tuvalu":                "tvl",
"Tuvinian":              "tyv",
"Twi":                   "twi",
"Udmurt":                "udm",
"Ugaritic":              "uga",
"Uighur":                "uig",
"Ukrainian":             "ukr",
"Umbundu":               "umb",
"Uncoded languages":     "mis",
"Undetermined language": "und",
"Upper Sorbian":         "hsb",
"Urdu":                  "urd",
"Uyghur":                "uig",
"Uzbek":                 "uzb",
"Vai":                   "vai",
"Valencian":             "cat",
"Venda":                 "ven",
"Vietnamese":            "vie",
"Volapuk":               "vol",
"Votic":                 "vot",
"Wakashan languages":    "wak",
"Walloon":               "wln",
"Waray-Waray":           "war",
"Washo":                 "was",
"Welsh":                 "wel",
"Western Frisian":       "fry",
"Wolaitta":              "wal",
"Wolaytta":              "wal",
"Wolof":                 "wol",
"Xhosa":                 "xho",
"Yakut":                 "sah",
"Yao":                   "yao",
"Yapese":                "yap",
"Yiddish":               "yid",
"Yoruba":                "yor",
"Yupik languages":       "ypk",
"Zande languages":       "znd",
"Zapotec":               "zap",
"Zaza":                  "zza",
"Zazaki":                "zza",
"Zenaga":                "zen",
"Zhuang":                "zha",
"Zulu":                  "zul",
"Zuni":                  "zun",
"creoles and pidgins":   "crp",
"tlhIngan-Hol":          "tlh",
}

if __name__=='__main__':
	keys = sorted(LANGUAGES_DICT.keys())
	print '[NSDictionary dictionaryWithObjectsAndKeys:'
	for key in keys:
		print '@"%s", @"%s",'%(LANGUAGES_DICT[key], key)
	print 'nil];'
