# RetroRevive — Hunt the Wumpus (1973/1978) Mechanics & Verification Specification

**Historical Origin:** Gregory Yob (1973, Dartmouth College / People's Computer Company)  
**Published in:** *Creative Computing* (1975) and *BASIC Computer Games: Microcomputer Edition*, ed. David H. Ahl (1978, pp. 178–181)  
**Engine Implementation:** `games/hunt_the_wumpus/engine.py` (100% Python Standard Library)  
**Graphical Interface:** `games/hunt_the_wumpus/app.py` (Pygame Desktop Experience)  
**Automated Tests:** `games/hunt_the_wumpus/test_engine.py` & `test_platform.py`  

---

## 1. Historical Provenance

In 1973, while visiting the People's Computer Company (PCC) in Menlo Park, California, **Gregory Yob** observed players growing weary of grid-based coordinate games like *Star Trek*, *Battleship*, and *Tic-Tac-Toe*. Seeking to pioneer non-Euclidean spatial navigation, Yob conceived a subterranean hunting game set inside a network of tunnels forming the vertices and edges of a **regular dodecahedron**.

David H. Ahl published Gregory Yob's game in *Creative Computing* and later in the legendary anthology *BASIC Computer Games: Microcomputer Edition* (1978, pp. 178–181). Hunt the Wumpus became an enduring cornerstone of computer gaming history, inspiring the interactive fiction genre, rogue-likes, and graph-theoretic game design.

RetroRevive preserves Gregory Yob's authentic 1978 topology, sensory proximity warnings, and crooked arrow ricochet rules, paired with an atmospheric cavern view and real-time planar Schlegel graph projection.

---

## 2. Cavern Topology: The Regular Dodecahedron

The cave system comprises exactly **20 rooms** (vertices) interconnected by **30 tunnels** (edges). Each room connects to exactly **3 other rooms** (degree 3):

```
                     [1]
                  /   |   \
               [2]   [5]   [8]
              /   \   |   /   \
           [3]    [10][4][6]   [9]
            |      |   \ /      |
           [12]   [11][14][15] [18]
             \     /   |   \   /
              [13][19][7] [16][17]
                 \   /      \  /
                     \  [20]  /
```

### 2.1. Complete 1978 Adjacency Matrix
Every tunnel is symmetric and bidirectional ($u \leftrightarrow v$):

| Room | Connected Adjacent Rooms | Room | Connected Adjacent Rooms |
|:---:|:---|:---:|:---|
| **1** | 2, 5, 8 | **11** | 10, 12, 19 |
| **2** | 1, 3, 10 | **12** | 3, 11, 13 |
| **3** | 2, 4, 12 | **13** | 12, 14, 20 |
| **4** | 3, 5, 14 | **14** | 4, 13, 15 |
| **5** | 1, 4, 6 | **15** | 6, 14, 16 |
| **6** | 5, 7, 15 | **16** | 15, 17, 20 |
| **7** | 6, 8, 17 | **17** | 7, 16, 18 |
| **8** | 1, 7, 9 | **18** | 9, 17, 19 |
| **9** | 8, 10, 18 | **19** | 11, 18, 20 |
| **10** | 2, 9, 11 | **20** | 13, 16, 19 |

---

## 3. Subterranean Hazards & Sensory Warnings

At mission initialization, 6 entities are assigned to distinct rooms chosen at random:
1. **The Hunter:** Starts in a room devoid of hazards with a quiver of 5 crooked arrows.
2. **The Wumpus:** A monstrous slumbering beast (1 room).
3. **Bottomless Pits:** Lethal chasms dropping into the earth (2 rooms).
4. **Super Bats:** Colonies of giant snatch-bats (2 rooms).

### 3.1. Proximity Sensory Warnings
When the hunter is in a room directly connected to a hazard (1 room distance), involuntary sensations alert the player:

| Hazard | Distance | Sensory Warning Text | Strategic Deduction |
|:---|:---:|:---|:---|
| **Wumpus** | 1 room | `"I smell a Wumpus!"` | The beast lurks in one of the 3 adjacent tunnels. |
| **Bottomless Pit** | 1 room | `"I feel a draft."` | At least one adjacent room contains a fatal pit. |
| **Super Bats** | 1 room | `"Bats nearby!"` | Giant snatch-bats flutter in an adjacent passage. |

Sensations do not reveal *which* of the three tunnels contains the hazard; deductive reasoning across multiple visited chambers is required.

---

## 4. Exploration & Movement Mechanics

When moving, the player enters one of the 3 rooms connected to the current chamber.

### 4.1. Hazard Encounters
- **Entering the Wumpus Room:**
  - The sleeping beast awakens and devours the hunter: `"TSK TSK TSK - WUMPUS GOT YOU!"` (Immediate defeat).
- **Entering a Bottomless Pit:**
  - The hunter falls into the abyss: `"YYYIIIIEEEE . . . FELL IN PIT"` (Immediate defeat).
- **Entering a Super Bat Colony:**
  - A giant bat seizes the hunter and flies them to an arbitrary room (1–20) chosen uniformly at random: `"ZAP--SUPER BAT SNATCH! ELSEWHEREVILLE FOR YOU!"`
  - The arrival room is resolved immediately:
    - If dropped into the Wumpus room $\rightarrow$ eaten.
    - If dropped into a Pit $\rightarrow$ fatal fall.
    - If dropped into the other bat room $\rightarrow$ snatched again.
    - If dropped into a safe room $\rightarrow$ exploration continues.

---

## 5. Crooked Arrow Ballistics

The hunter carries **5 Crooked Arrows**. These enchanted missiles can bend around corners and traverse through a chained sequence of 1 to 5 rooms.

### 5.1. Flight Trajectory & Ricochets
1. The player specifies a sequence of room numbers: $[R_1, R_2, \dots, R_k]$ where $1 \le k \le 5$.
2. The arrow launches from the hunter's chamber.
3. For each step:
   - If room $R_i$ is connected to the arrow's current chamber, the arrow travels smoothly into $R_i$.
   - **Ricochet:** If the player specifies a room that is **not connected** to the arrow's current chamber (or an invalid room number), the arrow ricochets off the stone walls and flies into a **random adjacent room**!
4. **Impact Outcomes:**
   - **Strikes Wumpus:** `"AHA! YOU GOT THE WUMPUS!"` $\rightarrow$ The beast is slain! **VICTORY!**
   - **Strikes Hunter:** `"OUCH! ARROW STRUCK YOU!"` $\rightarrow$ The arrow ricocheted back into the hunter's own chamber! **DEFEAT.**

### 5.2. Wumpus Awakening
If the arrow misses the Wumpus and the hunter survives:
- The sound of the clattering arrow disturbs the Wumpus.
- **75% Chance:** The Wumpus awakens and creeps into one of its 3 adjacent rooms chosen at random.
  - If it moves into the hunter's current room, it devours the hunter: `"TSK TSK TSK - WUMPUS GOT YOU!"`
- **25% Chance:** The Wumpus stays in its current chamber.
- **Arrow Exhaustion:** If all 5 arrows have been discharged without slaying the beast, the hunter is defenseless: `"YOU RAN OUT OF ARROWS!"` (Defeat).

---

## 6. Graphical Interface & Planar Schlegel Projection

`games/hunt_the_wumpus/app.py` renders the cave system through a dual perspective:
1. **Cavern Chamber (Left Pane):** Architectural stone archways representing the 3 tunnel portals, torch ember particle systems, and pulsating sensory warning banners.
2. **Subterranean Dodecahedron Chart (Right Pane):** A 2D Planar Schlegel diagram projecting the 3D dodecahedron onto a 2D plane:
   - Outer pentagon (Rooms 1, 2, 3, 4, 5)
   - Intermediate outer ring (Rooms 6, 7, 8, 9, 10)
   - Intermediate inner ring (Rooms 11, 12, 13, 14, 15)
   - Inner central pentagon (Rooms 16, 17, 18, 19, 20)
   - Interactive mouse selection for queueing crooked arrow flight paths.
