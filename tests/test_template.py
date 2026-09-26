import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from invitation import ROOT, handle_value, make_overlay


class TemplateTests(unittest.TestCase):
    def test_reject_path_traversal_and_invalid_handles(self):
        for value in ['../secret','hello/world','a b','a'*16,'']:
            with self.assertRaises(ValueError):handle_value(value)
        self.assertEqual(handle_value('@new_recipient'),'new_recipient')

    def test_long_handle_keeps_frame_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'overlay.png'
            qa=make_overlay({'handle':'WWWWWWWWWWWWWWW','avatar_path':str(ROOT/'examples/winchman.jpg')},json.loads((ROOT/'template.json').read_text()),out)
            im=Image.open(out)
            self.assertEqual(im.size,(1080,1920))
            a=im.getchannel('A')
            for box in [(0,0,1080,415),(0,1390,1080,1920),(0,0,210,1920),(855,0,1080,1920)]:
                self.assertIsNone(a.crop(box).getbbox())
            self.assertFalse(qa['avatar_below_display_resolution'])

    def test_small_avatar_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            Image.new('RGB',(100,100),'red').save(p/'avatar.png')
            qa=make_overlay({'handle':'test','avatar_path':str(p/'avatar.png')},json.loads((ROOT/'template.json').read_text()),p/'out.png')
            self.assertTrue(qa['avatar_below_display_resolution'])


if __name__=='__main__':unittest.main()
