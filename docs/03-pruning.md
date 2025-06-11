# Pruning

The generated opening tree has a lot of 1-game positions. Because it's difficult
to determine at processing time if a position will occur more than once. We can
set some sensible limits of the number of game moves to import, but without
prior knowledge of the coverage of the tree, we will still have lots of 1-game
positions.

So we have a `prune` command that will remove positions that have only been
reached once. But we don't want to remove all of them, just those positions
"far away" from the last position that has more than one game. That way, we
at least have space for the opening tree to grow as more opening discoveries
are made.

With a naive max-limit 60-ply import processing, the pruning gets rid of
98% of positions that are 1-game positions not close enough to the opening
tree branch.


## Pruning an opening tree

```
./tree.py prune \
    --db my_tree.db \
    --max-closeness 5 \
    --batch-size 2000
```
