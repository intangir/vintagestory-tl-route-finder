#!/usr/bin/python3

import json;
from math import ceil, sqrt

start = [5132, -12189];
dest = [2931, -11638];
start = [11370, -17825];
dest = [-2632, -4390];
#(start, dest) = ([-14979, -27061], [-16259, -26415])

#(start, dest) = ([-28750, -27062], [-1800, -51497])

# my farmstead to gearstead
(start, dest) = ([15053, 16015], [0, 0]);

# farmstead to some random arctic spot
(start, dest) = ([15053, 16015], [4559, -12239]);

# gearstead to archives
#(start, dest) = ([0,0], [156973,198624]);


jumplimit = 12;

tls = None;
crmat = None;


# gets the distance squared
def dist_squared(x1, y1, x2, y2):
    return (x1 - x2)**2 + (y1 - y2)**2;


# finds the closest pair of coordinates between two sets of coorindates
def find_closest(coords1, coords2):
    closest = None;
    for p1 in range(len(coords1)):
        for p2 in range(len(coords2)):
            sdist = dist_squared(*coords1[p1], *coords2[p2]);
            if(not closest or closest[0] > sdist):
                closest = [sdist, p1, p2];
    return closest;


# loads the translocator data from a json file
def LoadTLs():
    with open('translocators.geojson') as tlf:
        tlj = json.load(tlf);
    return tlj['features'];


# creates and fills a matrix of each TL vs every other TL and the shortest distances between its closest set of coordinates
def CalculateCrossReferenceDistanceMatrix(tls):
    print('calculating cross reference tls distance matrix');
    crmat = [[None for i in range(len(tls))] for j in range(len(tls))];

    for t1 in range(len(tls)):
        #if(tls[t1]["geometry"]["coordinates"] == []
        for t2 in range(t1+1, len(tls)):

            # find the shortest distance squared between the closest points between the two translocators
            closest = find_closest(tls[t1]["geometry"]["coordinates"], tls[t2]["geometry"]["coordinates"]);

            # save the closet distance between the two to both translocators
            crmat[t1][t2] = closest;
            crmat[t2][t1] = [closest[0], closest[2], closest[1]];

    return crmat;


def find_route(shortest, start_idx, dest_idx, jumplimit):
    global tls, crmat;
    # check the direct route

    shortest_sq = shortest**2;
    route = [start_idx, dest_idx];
    #print("\nstarting shortest ", route, "=", shortest, "limit =", jumplimit, end='');

    # first find shortest with only more 1 jump from 'here'
    # to hopefully cut down range to beat (so don't have to try as many routes)
    #if(jumplimit > 1):
    #    (shortest, route) = find_route(shortest, start_idx, dest_idx, 1) # (limited recursion to get min to beat)
    #    shortest_sq = shortest**2;

    # check through nearby TLs (at least 1 more jump)
    if(jumplimit > 0):
        for idx in range(len(crmat[start_idx])):
            d = crmat[start_idx][idx];
            if(d is None or crmat[idx] == crmat[dest_idx]):
                continue;
            # TL is within range
            if(d[0] < shortest_sq):
                #print('.', end='');
                walked = sqrt(d[0]);
                remaining = shortest - walked;
                if(jumplimit == 1):
                    # check only 1 jump from 'here'
                    to_dest_sq = crmat[idx][dest_idx][0];
                    if(to_dest_sq < remaining**2):
                        if(walked + sqrt(to_dest_sq) < shortest):
                            shortest = walked + sqrt(to_dest_sq);
                            shortest_sq = shortest**2;
                            route = [start_idx, idx, dest_idx];
                            #print("\n  new shortest ", route, "=", shortest, "limit =", jumplimit, end='');
                        else:
                            raise Exception("i don't think this comes up? (1)");
                else:
                    # checks multi jump routes (recursively)
                    (new_dist, new_route) = find_route(remaining, idx, dest_idx, jumplimit-1);
                    if(new_dist < remaining):
                        if(walked + new_dist < shortest):
                            shortest = walked + new_dist;
                            shortest_sq = shortest**2;
                            route = [start_idx] + new_route;
                            #print("\n  new shortest ", route, "=", shortest, "limit =", jumplimit, end='');
                        else:
                            raise Exception("i don't think this comes up? (2)");
                
    return (shortest, route);


def describe_route(route):
    global tls, crmat;
    leg = None;
    for i in range(0, len(route) - 1):
        idx = route[i];
        leg = crmat[idx][route[i+1]];
        at_coords = tls[idx]['geometry']['coordinates'][leg[1]].copy();
        to_coords = tls[route[i+1]]['geometry']['coordinates'][leg[2]].copy();
        at_coords[1] *= -1;
        to_coords[1] *= -1;
        print("start at" if idx < 0 else "warp to", at_coords);
        print("walk", ceil(sqrt(leg[0])), "blocks to", to_coords);


def main():
    global tls, crmat;
    
    tls = LoadTLs();

    # y coordinates are inexplicably reversed from what user sees...?!?!?!?!?!
    start[1] *= -1;
    dest[1] *= -1;

    # add the start and destination as coordinates in the TL to simplify the logic
    tls.append({'geometry': { 'coordinates': [dest] } });
    tls.append({'geometry': { 'coordinates': [start] } });

    crmat = CalculateCrossReferenceDistanceMatrix(tls);

    #from pprint import pprint;
    #pprint(crmat);

    shortest = sqrt(crmat[-2][-1][0]);
    print("by foot", ceil(shortest) )
    # finding shortest route
    print("finding quickest route using TLs...")
    try:
        for depth in range(jumplimit):
            (new_dist, new_route) = find_route(shortest, -1, -2, depth);
            if(new_dist < shortest):
                shortest = new_dist;
                route = new_route;
                print("new shortest:", ceil(shortest), "blocks, ", len(route), "jumps -", route);
    except KeyboardInterrupt:
        print("cancelled at depth", depth)
        pass;
    print("\nfound", ceil(shortest), route);

    describe_route(route);


main();
