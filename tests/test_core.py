import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from canned_beer.core import Sprite, layout, unique_names, xml_text


class LayoutTests(unittest.TestCase):
    def test_names(self):
        sprites = [Sprite(Path(p),1,1) for p in ['a.png','a.jpg','a_2.png','a.png']]
        self.assertEqual(unique_names(sprites), ['a','a_2','a_2_2','a_3'])

    def test_layout_bounds_and_spacing(self):
        sprites = [Sprite(Path(f'{i}.png'),w,h) for i,(w,h) in enumerate([(40,60),(70,20),(32,90),(10,15),(64,64)])]
        for mode in ['rows','grid','compact']:
            for size in [None,(300,300)]:
                w,h,ps = layout(sprites,mode,3,size)
                self.assertEqual(len(ps),len(sprites))
                for i,p in enumerate(ps):
                    self.assertGreaterEqual(p.x,0)
                    self.assertGreaterEqual(p.y,0)
                    self.assertLessEqual(p.x+p.sprite.width,w)
                    self.assertLessEqual(p.y+p.sprite.height,h)
                    for q in ps[i+1:]:
                        self.assertTrue(p.x+p.sprite.width+3 <= q.x or q.x+q.sprite.width+3 <= p.x or p.y+p.sprite.height+3 <= q.y or q.y+q.sprite.height+3 <= p.y)

    def test_overflow(self):
        for mode in ['rows','grid','compact']:
            with self.assertRaises(ValueError):
                layout([Sprite(Path('a.png'),65,65)],mode,size=(64,64))

    def test_xml(self):
        _,_,ps = layout([Sprite(Path('a&b.png'),20,30)])
        root = ET.fromstring(xml_text('sheet.png',ps))
        self.assertEqual(root.attrib['imagePath'],'sheet.png')
        self.assertEqual(root[0].attrib,dict(name='a&b',x='0',y='0',width='20',height='30'))


if __name__ == '__main__':
    unittest.main()
