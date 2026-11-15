"""APEX-SOCCERNOINTL-2026-11-15 (owner, "fix the other problems as well"): national-team games (World Cup qualifiers, Nations League,
friendlies) can't be graded from our box-score source (club leagues only) and have little player history, so they stay off the numbered
soccer boards and the cross-sport cards. is_national(team) = the team name is a country."""
import unicodedata, re
_N = """afghanistan albania algeria andorra angola antigua and barbuda argentina armenia aruba australia austria azerbaijan bahamas bahrain bangladesh
barbados belarus belgium belize benin bermuda bhutan bolivia bosnia and herzegovina bosnia herzegovina botswana brazil brunei bulgaria burkina faso burundi
cambodia cameroon canada cape verde cabo verde central african republic chad chile china china pr chinese taipei colombia comoros congo dr congo costa rica
cote d ivoire ivory coast croatia cuba curacao cyprus czechia czech republic denmark djibouti dominica dominican republic ecuador egypt el salvador england
equatorial guinea eritrea estonia eswatini ethiopia faroe islands fiji finland france gabon gambia georgia germany ghana gibraltar greece grenada guatemala
guinea guinea bissau guyana haiti honduras hong kong hungary iceland india indonesia iran iraq ireland republic of ireland rep ireland israel italy jamaica japan
jordan kazakhstan kenya kosovo kuwait kyrgyzstan laos latvia lebanon lesotho liberia libya liechtenstein lithuania luxembourg madagascar malawi malaysia maldives
mali malta mauritania mauritius mexico moldova mongolia montenegro morocco mozambique myanmar namibia nepal netherlands holland new zealand nicaragua niger nigeria
north korea korea dpr north macedonia macedonia northern ireland norway oman pakistan palestine panama papua new guinea paraguay peru philippines poland portugal
puerto rico qatar romania russia rwanda saudi arabia scotland senegal serbia seychelles sierra leone singapore slovakia slovenia solomon islands somalia
south africa south korea korea republic korea south sudan spain sri lanka sudan suriname sweden switzerland syria tahiti tajikistan tanzania thailand togo
trinidad and tobago trinidad tobago tunisia turkey turkiye turkmenistan uganda ukraine united arab emirates uae united states usa usmnt uruguay uzbekistan
vanuatu venezuela vietnam wales yemen zambia zimbabwe san marino new caledonia"""
NATIONS = set()
for _w in re.split(r"\s{2,}|\n", _N): pass
def _norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.sub(r'[^a-z ]', ' ', s).split())
# multi-word names are listed above with single spaces; match whole names against the joined list
_ALL = ' ' + ' '.join(_N.split()) + ' '
_MULTI = ["antigua and barbuda", "bosnia and herzegovina", "bosnia herzegovina", "burkina faso", "cape verde", "cabo verde", "central african republic", "china pr",
          "chinese taipei", "dr congo", "costa rica", "cote d ivoire", "ivory coast", "czech republic", "dominican republic", "el salvador", "equatorial guinea",
          "faroe islands", "guinea bissau", "hong kong", "republic of ireland", "rep ireland", "new zealand", "north korea", "korea dpr", "north macedonia",
          "northern ireland", "papua new guinea", "puerto rico", "saudi arabia", "sierra leone", "solomon islands", "south africa", "south korea", "korea republic",
          "south sudan", "sri lanka", "trinidad and tobago", "trinidad tobago", "united arab emirates", "united states", "san marino", "new caledonia"]
_MULTI_WORDS = set(w for m in _MULTI for w in m.split())
NATIONS = set(_MULTI) | set(w for w in _N.split() if w not in _MULTI_WORDS or w in ('guinea', 'congo', 'ireland', 'korea', 'sudan', 'china', 'georgia', 'macedonia'))
def is_national(team):
    t = _norm(team)
    return bool(t) and t in NATIONS
