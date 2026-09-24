import re

with open('/Users/mukhtarsyafii/.gemini/antigravity/brain/c6c68bbe-3cc9-4b15-b1f6-efcac2aafc9c/.system_generated/steps/10/content.md') as f:
    text = f.read()

# Search for the pattern like [21350203,"[0,0,\"1533663819\",[{\"1\":[[0,0,\"Dashboard\"
pattern = r'\[\d+,0,\\?"(\d+)\\?",\[\{\\?"1\\?":\[\[0,0,\\?"([^"\\]+)\\?"\]'
matches = re.findall(pattern, text)
print("Flexible matches:", matches)

# Fallback: look for 21350203
for m in re.finditer(r'21350203,"\[(\d+),0,\\?"(\d+)\\?",', text):
    gid = m.group(2)
    # search name near this
    snippet = text[m.end():m.end()+100]
    name_m = re.search(r'\[0,0,\\?"([^"\\]+)\\?"\]', snippet)
    name = name_m.group(1) if name_m else "unknown"
    print(f"GID: {gid} -> {name}")
