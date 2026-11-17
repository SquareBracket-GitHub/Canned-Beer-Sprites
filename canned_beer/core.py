from dataclasses import dataclass
from math import ceil, sqrt
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Sprite:
    path: Path
    width: int
    height: int


@dataclass(frozen=True)
class Placement:
    sprite: Sprite
    name: str
    x: int
    y: int


def unique_names(sprites):
    used = set()
    result = []
    for sprite in sprites:
        base = sprite.path.stem
        name = base
        index = 2
        while name in used:
            name = f"{base}_{index}"
            index += 1
        used.add(name)
        result.append(name)
    return result


def _pack(sprites, width, height, gap, mode):
    positions = {}
    if mode == "compact":
        free = [(0, 0, width, height)]
        order = sorted(range(len(sprites)), key=lambda i: sprites[i].width * sprites[i].height, reverse=True)
        for i in order:
            s = sprites[i]
            fits = [(min(w-s.width, h-s.height), w*h, n) for n, (x,y,w,h) in enumerate(free)
                    if s.width <= w and s.height <= h]
            if not fits:
                return None
            _, _, n = min(fits)
            x, y, _, _ = free[n]
            positions[i] = (x, y)
            right, bottom = x+s.width+gap, y+s.height+gap
            split = []
            for fx, fy, fw, fh in free:
                fr, fb = fx+fw, fy+fh
                if right <= fx or x >= fr or bottom <= fy or y >= fb:
                    split.append((fx,fy,fw,fh))
                    continue
                if x > fx: split.append((fx,fy,x-fx,fh))
                if right < fr: split.append((right,fy,fr-right,fh))
                if y > fy: split.append((fx,fy,fw,y-fy))
                if bottom < fb: split.append((fx,bottom,fw,fb-bottom))
            free = [r for j,r in enumerate(split) if not any(
                k != j and r[0]>=q[0] and r[1]>=q[1] and r[0]+r[2]<=q[0]+q[2]
                and r[1]+r[3]<=q[1]+q[3] and (r != q or k < j)
                for k,q in enumerate(split))]
    else:
        cell_w = max(s.width for s in sprites)
        cell_h = max(s.height for s in sprites)
        x = y = row_h = 0
        for i,s in enumerate(sprites):
            w,h = (cell_w,cell_h) if mode == "grid" else (s.width,s.height)
            if x+w > width:
                x = 0
                y += row_h+gap
                row_h = 0
            if w > width or y+h > height:
                return None
            positions[i] = (x,y)
            x += w+gap
            row_h = max(row_h,h)
    return positions


def layout(sprites, mode="rows", gap=0, size=None):
    if not sprites:
        raise ValueError("이미지를 추가해주세요.")
    if mode not in {"rows", "grid", "compact"} or gap < 0:
        raise ValueError("잘못된 배치 설정입니다.")
    if any(s.width <= 0 or s.height <= 0 for s in sprites):
        raise ValueError("이미지 크기가 올바르지 않습니다.")
    if size:
        width,height = size
        positions = _pack(sprites,width,height,gap,mode)
    else:
        area = sum((s.width+gap)*(s.height+gap) for s in sprites)
        width = max(max(s.width for s in sprites), ceil(sqrt(area)))
        limit = 16384
        width = min(width, limit)
        positions = None
        while width <= limit:
            positions = _pack(sprites,width,limit,gap,mode)
            if positions is not None:
                break
            if width == limit: break
            width = min(limit,width*2)
        if positions is not None:
            width = max(positions[i][0]+s.width for i,s in enumerate(sprites))
            height = max(positions[i][1]+s.height for i,s in enumerate(sprites))
    if positions is None:
        raise ValueError("이미지가 한 장에 모두 들어가지 않습니다. 시트 크기를 늘려주세요.")
    if width < 1 or height < 1 or width > 16384 or height > 16384 or width*height > 64*1024*1024:
        raise ValueError("시트는 한 변 16,384px, 총 64메가픽셀 이내로 지정해주세요.")
    names = unique_names(sprites)
    return width,height,[Placement(s,names[i],*positions[i]) for i,s in enumerate(sprites)]


def xml_text(image_name, placements):
    root = ET.Element("TextureAtlas", imagePath=image_name)
    for p in placements:
        ET.SubElement(root,"SubTexture",name=p.name,x=str(p.x),y=str(p.y),
                      width=str(p.sprite.width),height=str(p.sprite.height))
    ET.indent(root, space="  ")
    return ET.tostring(root,encoding="unicode",xml_declaration=True)
