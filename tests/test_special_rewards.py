"""Special chests must fund the next trial without duplicating rewards."""
import os
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import unittest
from systems.puzzle_level import PuzzleLevel


class SpecialRewardTests(unittest.TestCase):
    def test_every_special_chest_grants_both_potions_exactly_once(self):
        level=PuzzleLevel(seed=12)
        level.silver_keys=1
        next(o for o in level.objects if o.id=='special_entry_NW').interact(level)
        chests=[o for o in level.objects if o.type=='chest' and o.puzzle_id is None]
        self.assertEqual(len(chests),3)
        for chest in chests:
            before=(level.mode.poison_potions.count,level.mode.resurrection_potions.count)
            chest.interact(level)
            self.assertEqual((level.mode.poison_potions.count,level.mode.resurrection_potions.count),
                             (before[0]+1,before[1]+1))
            chest.interact(level)
            self.assertEqual((level.mode.poison_potions.count,level.mode.resurrection_potions.count),
                             (before[0]+1,before[1]+1))
        for pid in level.special_pid.values():
            chest=next(o for o in level.objects if o.id==pid+'_chest')
            before=(level.mode.poison_potions.count,level.mode.resurrection_potions.count)
            self.assertEqual(chest.interact(level),'locked')
            level.solve(pid,chest)
            self.assertEqual(chest.interact(level),'opened')
            self.assertEqual(chest.interact(level),'locked')
            self.assertEqual((level.mode.poison_potions.count,level.mode.resurrection_potions.count),
                             (before[0]+1,before[1]+1))

    def test_first_room_excluded_and_remaining_rooms_both_possible(self):
        for first in ('NW','NE','W'):
            counts={r:0 for r in ('NW','NE','W') if r!=first}
            for seed in range(120):
                level=PuzzleLevel(seed=seed)
                door=next(o for o in level.objects if o.id=='special_entry_'+first)
                initial=dict(level.special_content)
                self.assertEqual(door.interact(level),'locked')
                self.assertIsNone(level.first_special_room)
                self.assertEqual(initial,level.special_content)
                level.silver_keys=1
                self.assertEqual(door.interact(level),'open')
                self.assertEqual(level.first_special_room,first)
                self.assertNotEqual(level.gold_room,first)
                self.assertEqual(level.silver_keys,0)
                counts[level.gold_room]+=1
                selected=level.gold_room
                self.assertEqual(door.interact(level),'open')
                self.assertEqual(selected,level.gold_room)
                self.assertEqual(len([o for o in level.objects if o.key_id=='gold']),1)
                # A repeat interaction never changes either remaining room.
                self.assertIn(level.special_content[first],('statues','path'))
            for count in counts.values():
                self.assertGreater(count,35)
                self.assertLess(count,85)

    def test_first_trial_refunds_silver_and_gold_is_collectible_later(self):
        for first in ('NW','NE','W'):
            level=PuzzleLevel(seed=7)
            level.silver_keys=1
            next(o for o in level.objects if o.id=='special_entry_'+first).interact(level)
            decoy=next(o for o in level.objects if o.id==first+'_decoy')
            decoy.interact(level)
            pid=level.special_pid[first]
            chest=next(o for o in level.objects if o.id==pid+'_chest')
            level.solve(pid,chest)
            chest.interact(level)
            level.time+=.7
            next(o for o in level.objects if o.id==pid+'_key').interact(level)
            self.assertEqual(level.silver_keys,1)
            chosen=level.gold_room
            door=next(o for o in level.objects if o.id=='special_entry_'+chosen)
            self.assertEqual(door.interact(level),'open')
            self.assertEqual(level.gold_room,chosen)
            key=next(o for o in level.objects if o.key_id=='gold')
            self.assertEqual(key.interact(level),'locked')
            next(o for o in level.objects if o.id==chosen+'_goldchest').interact(level)
            level.time+=.7
            self.assertEqual(key.interact(level),'collected')
            self.assertEqual(key.interact(level),'locked')
            self.assertIn('gold',level.keys)
