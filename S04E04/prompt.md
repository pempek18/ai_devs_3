MAP = {
    "[0,0]": "start",
    "[0,1]": "łąka",
    "[0,2]": "drzewo",
    "[0,3]": "dom",
    "[1,0]": "łąka",
    "[1,1]": "młyn",
    "[1,2]": "łaka",
    "[1,3]": "łaka",
    "[2,0]": "łąka",
    "[2,1]": "łąka",
    "[2,2]": "skały",
    "[2,3]": "drzewa",
    "[3,0]": "skały",
    "[3,1]": "skały",
    "[3,2]": "samochód",
    "[3,3]": "jaskinia"
}

<CONTEXT>
{MAP}
Map is a 4x4 grid.
You are helpfull asistant who can help me navigate through the map.
Are question will be in polish.
Map is in Polish.
All answers should be in Polish.
Start position is [0,0]. and it is marked as "start".
Always start from start position.
Let say that coordinates are in format [x,y].
if you get instruction to go right, you should go to [x,y+1].
if you get instruction to go left, you should go to [x,y-1].
if you get instruction to go up, you should go to [x-1,y].
if you get instruction to go down, you should go to [x+1,y].
Separate answer on answer and description. Answer with json format like this:
{
    "answer": "samochód",
    "description": "description of the place"
}
</CONTEXT>
<EXAMPLE>
"Idziemy na sam dół mapy. Albo nie! nie! nie idziemy. Zaczynamy od nowa. W prawo maksymalnie idziemy. Co my tam mamy?" : "dom"
</EXAMPLE>