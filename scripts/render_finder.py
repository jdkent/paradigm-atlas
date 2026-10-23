"""Render site/task_finder.html from data/finder.json."""
html = open('scripts/finder_template.html').read().replace('__DATA__', open('data/finder.json').read().replace('</', '<\\/'))
open('site/task_finder.html', 'w').write(html); print(len(html))
