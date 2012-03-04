import codecs, commonscredits, urllib2

titles = [
    'File:Fuji_apple.jpg',
    'File:Banana_(white_background).jpg',
    'File:Black_hills_cat-tochichi.jpg',
    'File:Coin-img_2219.jpg',
    'File:Cowbird_egg.JPG',
    'File:Lemin_u0.gif',
    'File:Hargimont_051030_(5).JPG',
    'File:Bess2.jpg',
    'File:Igloo_outside.jpg',
    'File:Confituur.JPG',
    'File:Kangaroo1.jpg',
    'File:Lion_zoo_antwerp_1280.jpg',
    'File:Apodemus_sylvaticus_bosmuis.jpg',
    'File:Hausrotschwanz_Brutpflege_2006-05-24_211.jpg',
    'File:Wonder_octopus.jpg',
    'File:Pig_USDA01c0116.jpg',
    'File:Queen_Victoria_1887.jpg',
    'File:Road_in_Norway.jpg',
    'File:April_dawn.jpg',
    'File:Sea_Turtle.jpg',
    'File:Umbrella.png',
    'File:Augustine_Volcano_Jan_12_2006.jpg',
    'File:Gordijnen_aan_venster.JPG',
    'File:Kulintang_a_Kayo_01.jpg',
    'File:Wooden_yo-yo.jpg',
    'File:Zebra_rownikowa_Equus_burchelli_boehmi_RB3.jpg',

    'File:OtoHimeSoundMaker.jpg']

def write_html(htmlfilename, titles):
    fp = codecs.open(htmlfilename, encoding='utf-8', mode="w")

    commons = commonscredits.Commons()

    fp.write(u"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8" /></head>
<body>
<table>
""")

    for title in titles:
        fp.write(u"<tr>\n")
        fp.write(u"<td>%s</td>\n" % title)
        try:
            credits = commons.getCredits(title)
        except urllib2.HTTPError as e:
            fp.write(u"<td>[file not found!]</td>\n")
            continue

        fp.write(u"<td>%s</td>\n" % credits.credit_line())
        fp.write(u"</tr>\n")

    fp.write(u"""</table>
</body>
</html>""")

write_html('test.html', titles)

