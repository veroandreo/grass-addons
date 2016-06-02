#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       r.colors.matplotlib
# AUTHOR:       Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:      Use Matplotlib color tables to GRASS GIS
# COPYRIGHT:    (C) 2016 by Vaclav Petras and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Convert or apply a Matplotlib color table to a GRASS raster map
#% keyword: raster
#% keyword: color table
#% keyword: matplotlib
#%end

#%option G_OPT_R_MAPS
#% description: Raster map(s) to apply color table to
#% required: no
#% guisection: Basic
#%end
#%option G_OPT_F_OUTPUT
#% description: Name for the new color table rules file
#% required: no
#%end
#%option
#% key: color
#% type: string
#% label: Name of color table
#% description: Available color tables depend on the Matplotlib version
#% required: no
#% guisection: Basic
#%end

#%option
#% key: ncolors
#% type: integer
#% label: Number of colors in the color table
#% description: Number of color intervals in a discrete color table with -d
#% options: 2-
#% answer: 6
#% required: no
#% guisection: Rules
#%end
#%flag
#% key: d
#% label: Generate discrete color table
#% description: Generate discrete (interval) color table instead of a continuous one
#% guisection: Rules
#%end

#%flag
#% key: n
#% description: Reverse the order of colors (invert colors)
#% guisection: Basic
#%end
#%flag
#% key: g
#% description: Logarithmic scaling
#% guisection: Basic
#%end
#%flag
#% key: a
#% description: Logarithmic-absolute scaling
#% guisection: Basic
#%end
#%flag
#% key: e
#% description: Histogram equalization
#% guisection: Basic
#%end
#%rules
#% requires: -g, map
#% requires: -a, map
#% requires: -e, map
#%end


import os
import sys
import grass.script as gscript
import matplotlib.pyplot as plt


def values_to_rule(value, red, green, blue, percent):
    """Return textual representation of one color rule line"""
    return "{v:.3f}{p} {r}:{g}:{b}".format(v=value,
                                           p='%' if percent else '',
                                           r=red, g=green, b=blue)


# sync with r.colors.cubehelix
# this can potentially go to the core as something like grass.utils
def mpl_cmap_to_rules(cmap, n_colors=None, discrete=False, comments=None):
    if not n_colors:
        n_colors = cmap.N
    # determine numbers for recomputing from absolute range to relative
    cmin = 0
    cmax = n_colors
    if not discrete:
        cmax -= 1
    crange = cmax - cmin
    cinterval = float(crange) / n_colors

    rules = []
    if comments:
        for comment in comments:
            rules.append("# {}".format(comment))
    for v1 in range(0, n_colors, 1):
        r1, g1, b1 = cmap(v1)[:3]
        if discrete:
            v2 = v1 + cinterval
        v1 = 100 * (crange - (cmax - v1)) / float(crange)
        if discrete:
            v2 = 100 * (crange - (cmax - v2)) / float(crange)

        r1 = int(r1 * 255)
        g1 = int(g1 * 255)
        b1 = int(b1 * 255)
        rules.append(values_to_rule(value=v1, red=r1, green=g1,
                                    blue=b1, percent=True))
        if discrete:
            rules.append(values_to_rule(value=v2, red=r1, green=g1,
                                        blue=b1, percent=True))
    return '\n'.join(rules)


def main(options, flags):
    name = options['color']
    n_colors = int(options['ncolors'])
    discrete = flags['d']

    if flags['n']:
        name += '_r'

    cmap = plt.get_cmap(name, lut=n_colors)

    comments = []
    comments.append(
        "Generated from Matplotlib color table <{}>".format(name))
    comments.append(
        "using:")
    command = [sys.argv[0].split(os.path.sep)[-1]]
    command.extend(sys.argv[1:])
    comments.append(
        "  {}".format(' '.join(command)))

    rules = mpl_cmap_to_rules(cmap, n_colors=n_colors,
                              discrete=discrete, comments=comments)

    if options['map']:
        rcf = ''
        for char in 'gae':
            if flags[char]:
                rcf += char
        gscript.write_command('r.colors', map=options['map'], flags=rcf,
                              rules='-', stdin=rules,)
    if options['output']:
        with open(options['output'], 'w') as f:
            f.write(rules)
            f.write('\n')
    elif not options['map']:
        print rules


if __name__ == '__main__':
    sys.exit(main(*gscript.parser()))