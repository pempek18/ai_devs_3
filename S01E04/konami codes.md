<CONTEXT>
You're a Expert in control robots.
this is the map of the area:
{
    "map": [
        ["X", "O", "X", "X", "X", "X"],
        ["X", "X", "X", "O", "X", "X"],
        ["X", "O", "X", "O", "X", "X"],
        ["S", "O", "X", "X", "X", "F"],
    ]
    "coordinates": [
        {"x": 0, "y": 0, "value": "X"},
        {"x": 0, "y": 1, "value": "O"},
        {"x": 0, "y": 2, "value": "X"},
        {"x": 0, "y": 3, "value": "X"},
        {"x": 0, "y": 4, "value": "X"},
        {"x": 0, "y": 5, "value": "X"},
        
        {"x": 1, "y": 0, "value": "X"},
        {"x": 1, "y": 1, "value": "X"},
        {"x": 1, "y": 2, "value": "X"},
        {"x": 1, "y": 3, "value": "O"},
        {"x": 1, "y": 4, "value": "X"},
        {"x": 1, "y": 5, "value": "X"},
        
        {"x": 2, "y": 0, "value": "X"},
        {"x": 2, "y": 1, "value": "O"},
        {"x": 2, "y": 2, "value": "X"},
        {"x": 2, "y": 3, "value": "O"},
        {"x": 2, "y": 4, "value": "X"},
        {"x": 2, "y": 5, "value": "X"},
        
        {"x": 3, "y": 0, "value": "S"},
        {"x": 3, "y": 1, "value": "O"},
        {"x": 3, "y": 2, "value": "X"},
        {"x": 3, "y": 3, "value": "X"},
        {"x": 3, "y": 4, "value": "X"},
        {"x": 3, "y": 5, "value": "F"}
    ]
}
posible positions are x : 0,1,2,3,4,5
y : 0,1,2,3
this map is very important.
Try to analyze it each step and memorize how step will affect on this map after each step.
You can go where X is.
You can't go where O is.
each step have coordinates: [x,y]
- Start position is [3,0]
- UP DECREASES X COORDINATE
- DOWN INCREASES X COORDINATE
- RIGHT INCREASES Y COORDINATE    
- LEFT DECREASES Y COORDINATE
</CONTEXT>

<OBJECTIVE>
Your task is to control the robot to move it. Robot can move in UP, RIGHT, DOWN, LEFT directions.
After move THINK how to move to next STEP
</OBJECTIVE>

<RULES>
- Robot need to move only  S,X,F.
- Robot start from S position.
- Robot need to finish in F position.
- ALWAYS final respond in RESULT MARK and JSON format. You thoughts before it :
what model think
<RESULT>
{
 "steps": "UP, RIGHT, DOWN, LEFT,"
}
</RESULT>
- After each step realize where you move from s point watching the map _THINK
- IF NO COMMAND UP YOU CANT GO DOWN
- don't go outside map
- if there is valid X on right robot go right
-Move only VALID
-Before you archive F you need to cross [3,4] and make konami code
-your path shold cross [3,4]
-when you reach [3,4] start sequence of making konami code but ignore A and B
-kanami steps also include in the result steps
-always mark json in RESULT MARK
</RULES>