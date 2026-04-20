import json

with open('output/wall_blocks.json') as f:
    d = json.load(f)

blocks = d['blocks']
print(f"// {len(blocks)} 个墙壁块")
print("const mazeBlocks = [")
for b in blocks:
    print(f"  {{x:{b['x']},y:{b['y']},w:{b['w']},h:{b['h']}}},")
print("]")
