window.RECOLOR = {
 "ground": "b19d86",
 "ref": {
  "fur": [
   "645055",
   "746065",
   "836d77",
   "917a86"
  ],
  "belly": [
   "9c8491",
   "a38c99",
   "ab96a3",
   "b7a7b4"
  ],
  "stripe": [
   "2f273b",
   "41374c",
   "4f404b",
   "57454b"
  ],
  "eye": "756667",
  "stats": {
   "fur_L": [
    0.4402725111059595,
    0.5744074587929232,
    0.7314080462335794
   ],
   "stripe_L": 0.3624036344303659,
   "ground_L": 0.690015716218267,
   "tiger_C": 0.034524517669898544
  }
 },
 "passes": [
  {
   "id": "base",
   "title": "Original palette",
   "changed": "The palette from tiger.json: orange-salmon fur, pink belly, near-black stripes, golden eye. Stripes are now rendered (opt-in flag in render.py).",
   "look": "Grayscale on the gold ground: fur and ground sit at nearly the same value, so the sprite dissolves into the backdrop.",
   "palette": {
    "fur": [
     "7a4636",
     "b06a54",
     "d89478",
     "efbc9c"
    ],
    "belly": [
     "9a7080",
     "c496a2",
     "e0b8bc",
     "f4d8d4"
    ],
    "stripe": [
     "0a0a16",
     "161628",
     "26263c",
     "3a3a52"
    ],
    "eye": "d8a828",
    "outline": "1a1018"
   },
   "metrics": {
    "colors": 14,
    "ref_dist": 4.3,
    "min_step": 11.0,
    "ground_gap": 5.0,
    "hue_drift": 16.0,
    "loud": 0.3,
    "eye_chroma": 0.144
   }
  },
  {
   "id": "value",
   "title": "Value structure",
   "changed": "Lightness only: four even steps per ramp, stripes well below the darkest fur, belly clearly lighter, darker outline. Hue and chroma untouched.",
   "look": "Squint. Do the stripes read? Are all four shading steps visible on the body? Is there a gap to the ground?",
   "palette": {
    "fur": [
     "582819",
     "84432e",
     "a8684d",
     "ca9879"
    ],
    "belly": [
     "785060",
     "a47884",
     "c69fa3",
     "e5cac6"
    ],
    "stripe": [
     "05050f",
     "0f0f21",
     "1d1c32",
     "2b2b42"
    ],
    "eye": "d8a828",
    "outline": "0a0309"
   },
   "metrics": {
    "colors": 14,
    "ref_dist": 4.4,
    "min_step": 12.0,
    "ground_gap": 19.0,
    "hue_drift": 15.0,
    "loud": 0.3,
    "eye_chroma": 0.144
   }
  },
  {
   "id": "temperature",
   "title": "Temperature",
   "changed": "Fur and belly shadows drift toward violet and gain chroma; highlights drift toward yellow and lose it. Stripes become indigo instead of black; the outline turns indigo too.",
   "look": "Does form turn from warm to cool without relying on darkness alone?",
   "palette": {
    "fur": [
     "601e27",
     "8b3c33",
     "a7684b",
     "bc9f80"
    ],
    "belly": [
     "764e6f",
     "a6768b",
     "c69fa2",
     "e0ccc5"
    ],
    "stripe": [
     "030318",
     "0b0e29",
     "181d37",
     "272c44"
    ],
    "eye": "d8a828",
    "outline": "060313"
   },
   "metrics": {
    "colors": 14,
    "ref_dist": 4.8,
    "min_step": 12.0,
    "ground_gap": 19.0,
    "hue_drift": 53.0,
    "loud": 11.0,
    "eye_chroma": 0.144
   }
  },
  {
   "id": "chroma",
   "title": "Chroma budget",
   "changed": "Fur chroma cut by 45%, belly by 50%. The eye is raised to a high-chroma amber: the only loud color.",
   "look": "Mute everything mentally: does the eye still pull first, and does the body feel calm?",
   "palette": {
    "fur": [
     "502c2f",
     "764b45",
     "947162",
     "b2a191"
    ],
    "belly": [
     "6a5667",
     "977e88",
     "b9a5a6",
     "d8cfcb"
    ],
    "stripe": [
     "030318",
     "0b0e29",
     "181d37",
     "272c44"
    ],
    "eye": "e6b731",
    "outline": "060313"
   },
   "metrics": {
    "colors": 14,
    "ref_dist": 2.6,
    "min_step": 12.0,
    "ground_gap": 19.0,
    "hue_drift": 51.0,
    "loud": 0.3,
    "eye_chroma": 0.15
   }
  },
  {
   "id": "mother",
   "title": "Mother color",
   "changed": "A small offset toward the painting's gold ground is added to fur, belly and stripes, so the tiger and its ground share a pigment.",
   "look": "Do the sprite and the gold feel like one painting rather than a cutout on a backdrop?",
   "palette": {
    "fur": [
     "56291f",
     "7e4734",
     "9d6e50",
     "bc9f80"
    ],
    "belly": [
     "725458",
     "a07c79",
     "c3a396",
     "e3ccba"
    ],
    "stripe": [
     "07040f",
     "120f1f",
     "201c2c",
     "2f2b38"
    ],
    "eye": "e6b731",
    "outline": "060313"
   },
   "metrics": {
    "colors": 14,
    "ref_dist": 3.6,
    "min_step": 12.0,
    "ground_gap": 19.0,
    "hue_drift": 35.0,
    "loud": 0.3,
    "eye_chroma": 0.15
   }
  },
  {
   "id": "reference",
   "title": "Match the reference",
   "changed": "Hue and chroma pulled 70% toward the colors sampled from the painting's tiger (mauve fur, indigo stripes); our values and our loud eye stay.",
   "look": "Compare against the painting itself. Where does the sprite still disagree: value, warmth, or saturation?",
   "palette": {
    "fur": [
     "4a3030",
     "6d4f4d",
     "8f7270",
     "b79d9e"
    ],
    "belly": [
     "6e5660",
     "987e86",
     "bca3a9",
     "decbcf"
    ],
    "stripe": [
     "080311",
     "150d1f",
     "251b27",
     "362931"
    ],
    "eye": "e6b731",
    "outline": "060313"
   },
   "metrics": {
    "colors": 14,
    "ref_dist": 0.9,
    "min_step": 12.0,
    "ground_gap": 19.0,
    "hue_drift": 4.0,
    "loud": 0.3,
    "eye_chroma": 0.15
   }
  }
 ]
};
