from django.core.management.base import BaseCommand
from navigation.models import Building, Waypoint, Edge
import math


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


BUILDINGS = [
    # Gates & Main Entrances
    {'name': 'Main Gate', 'short_name': 'Gate', 'category': 'other',
     'description': 'Main entrance to Caleb University campus',
     'latitude': 6.667474120572148, 'longitude': 3.6410443393112177},

    # Academic Buildings
    {'name': 'E-Library', 'short_name': 'ELibrary', 'category': 'academic',
     'description': 'Electronic library and study resource centre',
     'latitude': 6.669760464541191, 'longitude': 3.637103669013986},
    {'name': 'COPAS Building', 'short_name': 'COPAS', 'category': 'academic',
     'description': 'College of Pure and Applied Sciences',
     'latitude': 6.670202697638871, 'longitude': 3.6373557966518857},
    {'name': 'Architecture Building', 'short_name': 'Architecture', 'category': 'academic',
     'description': 'Department of Architecture',
     'latitude': 6.670931667, 'longitude': 3.638628333},
    {'name': 'JUPEB Building', 'short_name': 'JUPEB', 'category': 'academic',
     'description': 'JUPEB programme building',
     'latitude': 6.671246667, 'longitude': 3.639013333},
    {'name': 'Mass Communication Building', 'short_name': 'MassCom', 'category': 'academic',
     'description': 'Mass Communication department building',
     'latitude': 6.668800000, 'longitude': 3.636836667},
    {'name': 'Psychology & Criminology Building', 'short_name': 'PsychCrim', 'category': 'academic',
     'description': 'Psychology and Criminology department',
     'latitude': 6.670145000, 'longitude': 3.639200000},
    {'name': 'Nursing Building', 'short_name': 'Nursing', 'category': 'academic',
     'description': 'Nursing department building',
     'latitude': 6.670425000, 'longitude': 3.639011667},
    {'name': 'Main Library', 'short_name': 'Library', 'category': 'academic',
     'description': 'Main library and Caleb University distance learning centre',
     'latitude': 6.667905000, 'longitude': 3.635798333},
    {'name': 'Admin Block', 'short_name': 'Admin', 'category': 'administrative',
     'description': 'University administration building',
     'latitude': 6.669663333, 'longitude': 3.637096667},
    {'name': 'Caleb Alumni Network Office', 'short_name': 'Alumni', 'category': 'administrative',
     'description': 'Caleb Alumni Network Office',
     'latitude': 6.669654400, 'longitude': 3.637576550},

    # Worship & Events
    {'name': 'Auditorium / Chapel', 'short_name': 'Chapel', 'category': 'religious',
     'description': 'University chapel and main auditorium — front entrance',
     'latitude': 6.670445000, 'longitude': 3.636055000},

    # Facilities
    {'name': 'New Cafeteria', 'short_name': 'NewCafe', 'category': 'facility',
     'description': 'New university cafeteria',
     'latitude': 6.671283333, 'longitude': 3.636038333},
    {'name': 'Bakery', 'short_name': 'Bakery', 'category': 'facility',
     'description': 'University bakery',
     'latitude': 6.670816667, 'longitude': 3.635151667},
    {'name': 'Sports Complex', 'short_name': 'Sports', 'category': 'sport',
     'description': 'University sports and recreation facility',
     'latitude': 6.669078465717958, 'longitude': 3.633879653831855},
    {'name': 'Basketball Court', 'short_name': 'Basketball', 'category': 'sport',
     'description': 'Basketball court',
     'latitude': 6.668228290, 'longitude': 3.635680170},
    {'name': 'Medical Centre', 'short_name': 'Medical', 'category': 'medical',
     'description': 'University medical centre',
     'latitude': 6.669751667, 'longitude': 3.639591667},
    {'name': 'Sterling Bank', 'short_name': 'Bank', 'category': 'facility',
     'description': 'Sterling Bank on campus',
     'latitude': 6.668528333, 'longitude': 3.639005000},
    {'name': 'Mobile ATM', 'short_name': 'ATM', 'category': 'facility',
     'description': 'Mobile ATM point',
     'latitude': 6.668558333, 'longitude': 3.638975000},

    # Female Hostels
    {'name': 'Susan Hall', 'short_name': 'Susan', 'category': 'hostel',
     'description': 'Female student hostel',
     'latitude': 6.668699680, 'longitude': 3.639460380},
    {'name': 'Mary Hall', 'short_name': 'Mary', 'category': 'hostel',
     'description': 'Female student hostel',
     'latitude': 6.667392970, 'longitude': 3.638045110},
    {'name': 'Rebecca Hall', 'short_name': 'Rebecca', 'category': 'hostel',
     'description': 'Female student hostel',
     'latitude': 6.667030200, 'longitude': 3.638433920},
    {'name': 'Deborah Hall', 'short_name': 'Deborah', 'category': 'hostel',
     'description': 'Female student hostel',
     'latitude': 6.667804980, 'longitude': 3.637471130},
    {'name': 'Esme Hall', 'short_name': 'Esme', 'category': 'hostel',
     'description': 'Female student hostel',
     'latitude': 6.667119820, 'longitude': 3.636738680},
    {'name': 'Mercy Hall', 'short_name': 'Mercy', 'category': 'hostel',
     'description': 'Female student hostel',
     'latitude': 6.666772260, 'longitude': 3.637158240},

    # Male Hostels
    {'name': 'Joshua Hall', 'short_name': 'Joshua', 'category': 'hostel',
     'description': 'Male student hostel',
     'latitude': 6.671516667, 'longitude': 3.635661667},
    {'name': 'Joseph Hall', 'short_name': 'Joseph', 'category': 'hostel',
     'description': 'Male student hostel',
     'latitude': 6.671781667, 'longitude': 3.635396667},
    {'name': 'Elisha Hall', 'short_name': 'Elisha', 'category': 'hostel',
     'description': 'Male student hostel',
     'latitude': 6.672206667, 'longitude': 3.635036667},
    {'name': 'Levi Hall', 'short_name': 'Levi', 'category': 'hostel',
     'description': 'Male student hostel',
     'latitude': 6.672691667, 'longitude': 3.634570000},
    {'name': 'Integrity Hall', 'short_name': 'Integrity', 'category': 'hostel',
     'description': 'Male student hostel',
     'latitude': 6.671968333, 'longitude': 3.634451667},
    {'name': 'Staff Residence', 'short_name': 'Staff', 'category': 'other',
     'description': 'Staff residential quarters',
     'latitude': 6.672413857174871, 'longitude': 3.6365350406549233},
]

# (name, lat, lng)
WAYPOINTS = [
    # Building entrances — these match short_name + ' Entrance' pattern
    # Junctions — named descriptively
    ('J-Gate-Main', 6.667474120572148, 3.6410443393112177),

    # Female hostel area
    ('J-Susan-Car-Entrance', 6.668408100, 3.639690070),
    ('J-Uturn-1', 6.668043333, 3.640005000),
    ('J-Uturn-2', 6.668653333, 3.639361667),
    ('J-Sterling-Parking', 6.668535000, 3.639086667),
    ('J-Female-Hostel-Sterling', 6.668598333, 3.639183333),
    ('J-Rebecca-Entrance', 6.667127770, 3.638449440),
    ('J-Mary-Entrance', 6.667378400, 3.638342690),
    ('J-Mary-Roundabout', 6.667587100, 3.638176770),
    ('J-Deborah-Entrance', 6.668079270, 3.637623820),
    ('J-Mercy-Entrance', 6.666814140, 3.637153980),
    ('J-Esme-Entrance', 6.667123930, 3.636890210),

    # Main road junctions
    ('J-Roundabout-Main', 6.669258333, 3.638421667),
    ('J-Behind-Roundabout', 6.669560230, 3.638435650),
    ('J-Path-Gate-Medical', 6.669420000, 3.638501667),
    ('J-Y-Psych-Nursing-Medical', 6.669408333, 3.638675000),
    ('J-To-Medical', 6.669480000, 3.638641667),
    ('J-Medical-Entrance', 6.669623333, 3.639596667),
    ('J-Medical-Nursing-Psych', 6.669583333, 3.639271667),
    ('J-Psych-Crim-Junction', 6.669761667, 3.639061667),
    ('J-Nursing-Car-Entrance', 6.670096667, 3.638811667),
    ('J-Psych-Nursing-Turn', 6.669496040, 3.639357060),
    ('J-LoveGarden-Nursing', 6.670334630, 3.638414110),
    ('J-Arch-Junction', 6.670753333, 3.638186667),
    ('J-LoveGarden-T', 6.670042740, 3.638178030),
    ('J-School-Entrance', 6.670280840, 3.637947250),
    ('J-Love-Garden', 6.670288010, 3.637923460),
    ('J-LoveGarden-Arch-School', 6.670417710, 3.637798090),
    ('J-LoveGarden-Path', 6.670608333, 3.638081667),
    ('J-Arch-Main-Path', 6.670808333, 3.638161667),
    ('J-Arch-Into', 6.671016667, 3.638550000),
    ('J-Middle-Standpoint', 6.670681740, 3.637657910),
    ('J-Bushy-NewCafe', 6.670651667, 3.637725000),
    ('J-School-Side-Path', 6.670543333, 3.637598333),
    ('J-School-NewCafe-Paved', 6.670250000, 3.637075000),

    # Admin area
    ('J-Admin-MainRoad', 6.669888333, 3.636725000),
    ('J-Admin-Plus', 6.669925780, 3.636837650),
    ('J-Admin-MainRoad-2', 6.669298333, 3.637408333),
    ('J-Admin-MainRoad-3', 6.669040000, 3.637740000),
    ('J-School-Admin-Side', 6.669666810, 3.637615380),
    ('J-School-T', 6.669333350, 3.637432850),
    ('J-Admin-Side-Entry', 6.670255000, 3.637208333),
    ('J-CarPark', 6.670138333, 3.636503333),

    # MassCom area
    ('J-MassCom-FemaleHostel', 6.669296667, 3.637108333),
    ('J-MassCom-Into', 6.669113333, 3.636936667),
    ('J-MassCom-Entrance-1', 6.668905000, 3.636991667),
    ('J-MassCom-Entrance-2', 6.668651667, 3.637165000),
    ('J-4Way-FemaleHostel-MassCom-Sports', 6.668890000, 3.635913333),
    ('J-Bushy-Auditorium-MassCom-Sports', 6.669063333, 3.635765000),

    # Auditorium / Chapel
    ('J-Chapel-Back-Entrance', 6.670188333, 3.635688333),
    ('J-Chapel-Sports-Path', 6.670323333, 3.635425000),

    # Bakery / New Cafe / Male hostel area
    ('J-Bakery-Entrance', 6.670895000, 3.635083333),
    ('J-3Way-Road-Cafe-Chapel', 6.670710000, 3.635816667),
    ('J-NewCafe-Paved', 6.671058333, 3.636338333),
    ('J-NewCafe-Side-Entrance', 6.671373333, 3.636541667),
    ('J-NewCafe-Back-Entrance', 6.671816667, 3.636545000),
    ('J-BoyHostel-From-Cafe', 6.671301667, 3.635841667),
    ('J-Integrity-From-BoyHostel', 6.671786667, 3.635186667),
    ('J-Integrity-From-Bakery', 6.671140000, 3.634843333),
    ('J-Integrity-Turn', 6.671368333, 3.634936667),
]

MANUAL_EDGES = [
    # === GATE AREA ===
    ('Gate Entrance', 'J-Gate-Main'),
    ('J-Gate-Main', 'J-Uturn-1'),
    ('J-Uturn-1', 'J-Uturn-2'),
    ('J-Uturn-2', 'J-Susan-Car-Entrance'),
    ('J-Susan-Car-Entrance', 'Susan Entrance'),
    ('J-Uturn-2', 'J-Female-Hostel-Sterling'),
    ('J-Female-Hostel-Sterling', 'J-Sterling-Parking'),
    ('J-Sterling-Parking', 'Bank Entrance'),
    ('J-Sterling-Parking', 'ATM Entrance'),

    # === ROUNDABOUT / MAIN ROAD ===
    ('J-Female-Hostel-Sterling', 'J-Roundabout-Main'),
    ('J-Roundabout-Main', 'J-Behind-Roundabout'),
    ('J-Roundabout-Main', 'J-Path-Gate-Medical'),
    ('J-Path-Gate-Medical', 'J-Y-Psych-Nursing-Medical'),
    ('J-Y-Psych-Nursing-Medical', 'J-To-Medical'),
    ('J-To-Medical', 'J-Psych-Nursing-Turn'),
    ('J-Psych-Nursing-Turn', 'J-Medical-Entrance'),
    ('J-Medical-Entrance', 'Medical Entrance'),
    ('Medical Entrance', 'Medical Centre'),
    ('J-Psych-Nursing-Turn', 'J-Medical-Nursing-Psych'),
    ('J-Medical-Nursing-Psych', 'J-Psych-Crim-Junction'),
    ('J-Psych-Crim-Junction', 'PsychCrim Entrance'),
    ('J-Psych-Crim-Junction', 'J-Nursing-Car-Entrance'),
    ('J-Nursing-Car-Entrance', 'Nursing Entrance'),
    ('J-Y-Psych-Nursing-Medical', 'J-LoveGarden-Nursing'),
    ('J-LoveGarden-Nursing', 'Nursing Entrance'),
    ('J-LoveGarden-Nursing', 'J-Arch-Junction'),
    ('J-Arch-Junction', 'J-Arch-Main-Path'),
    ('J-Arch-Main-Path', 'J-Arch-Into'),
    ('J-Arch-Into', 'Architecture Entrance'),
    ('Architecture Entrance', 'JUPEB Entrance'),

    # === ADMIN AREA ===
    ('J-Behind-Roundabout', 'J-School-Admin-Side'),
    ('J-School-Admin-Side', 'Alumni Entrance'),
    ('J-School-Admin-Side', 'J-School-T'),
    ('J-School-T', 'J-Admin-MainRoad-2'),
    ('J-Admin-MainRoad-2', 'J-Admin-MainRoad-3'),
    ('J-Admin-MainRoad-3', 'J-4Way-FemaleHostel-MassCom-Sports'),
    ('J-Admin-MainRoad', 'J-Admin-Plus'),
    ('J-Admin-Plus', 'Admin Entrance'),
    ('J-Admin-Plus', 'J-Admin-Side-Entry'),
    ('J-Admin-Side-Entry', 'ELibrary Entrance'),
    ('J-Admin-MainRoad', 'J-CarPark'),
    ('J-School-T', 'J-Admin-MainRoad'),
    ('J-School-T', 'J-MassCom-FemaleHostel'),

    # === SCHOOL BUILDING / LOVE GARDEN ===
    ('J-Admin-Side-Entry', 'J-School-NewCafe-Paved'),
    ('J-School-NewCafe-Paved', 'J-School-Entrance'),
    ('J-School-Entrance', 'J-Love-Garden'),
    ('J-Love-Garden', 'J-LoveGarden-T'),
    ('J-LoveGarden-T', 'J-LoveGarden-Arch-School'),
    ('J-LoveGarden-Arch-School', 'J-Middle-Standpoint'),
    ('J-Middle-Standpoint', 'J-Bushy-NewCafe'),
    ('J-Middle-Standpoint', 'J-School-Side-Path'),
    ('J-Middle-Standpoint', 'J-LoveGarden-Path'),
    ('J-LoveGarden-Path', 'J-Arch-Main-Path'),
    ('J-Bushy-NewCafe', 'J-NewCafe-Paved'),
    ('J-NewCafe-Paved', 'NewCafe Entrance'),
    ('J-NewCafe-Paved', 'J-NewCafe-Side-Entrance'),
    ('J-NewCafe-Side-Entrance', 'J-NewCafe-Back-Entrance'),

    # === MASS COM AREA ===
    ('J-MassCom-FemaleHostel', 'J-MassCom-Into'),
    ('J-MassCom-Into', 'J-MassCom-Entrance-1'),
    ('J-MassCom-Entrance-1', 'MassCom Entrance'),
    ('J-MassCom-Into', 'J-MassCom-Entrance-2'),
    ('J-MassCom-Entrance-2', 'MassCom Entrance'),
    ('J-Admin-MainRoad-3', 'J-MassCom-FemaleHostel'),
    ('J-MassCom-FemaleHostel', 'J-4Way-FemaleHostel-MassCom-Sports'),

    # === FEMALE HOSTEL LINE ===
    ('J-4Way-FemaleHostel-MassCom-Sports', 'J-Esme-Entrance'),
    ('J-Esme-Entrance', 'Esme Entrance'),
    ('J-Esme-Entrance', 'J-Mercy-Entrance'),
    ('J-Mercy-Entrance', 'Mercy Entrance'),
    ('J-4Way-FemaleHostel-MassCom-Sports', 'J-Mary-Roundabout'),
    ('J-Mary-Roundabout', 'J-Mary-Entrance'),
    ('J-Mary-Entrance', 'Mary Entrance'),
    ('J-Mary-Roundabout', 'J-Rebecca-Entrance'),
    ('J-Rebecca-Entrance', 'Rebecca Entrance'),
    ('J-Mary-Roundabout', 'J-Deborah-Entrance'),
    ('J-Deborah-Entrance', 'Deborah Entrance'),

    # === CHAPEL / AUDITORIUM ===
    ('J-4Way-FemaleHostel-MassCom-Sports', 'J-Bushy-Auditorium-MassCom-Sports'),
    ('J-Bushy-Auditorium-MassCom-Sports', 'J-Chapel-Back-Entrance'),
    ('J-Chapel-Back-Entrance', 'Chapel Entrance'),
    ('Chapel Entrance', 'J-Chapel-Sports-Path'),
    ('J-Chapel-Sports-Path', 'J-3Way-Road-Cafe-Chapel'),
    ('J-3Way-Road-Cafe-Chapel', 'J-Bakery-Entrance'),
    ('J-Bakery-Entrance', 'Bakery Entrance'),
    ('J-3Way-Road-Cafe-Chapel', 'J-NewCafe-Paved'),
    ('J-CarPark', 'J-3Way-Road-Cafe-Chapel'),

    # === SPORTS COMPLEX ===
    ('J-Chapel-Sports-Path', 'Sports Entrance'),
    ('J-Bushy-Auditorium-MassCom-Sports', 'Sports Entrance'),
    ('Sports Entrance', 'Basketball Entrance'),

    # === LIBRARY ===
    ('J-4Way-FemaleHostel-MassCom-Sports', 'Library Entrance'),

    # === MALE HOSTELS ===
    ('J-BoyHostel-From-Cafe', 'Joshua Entrance'),
    ('J-BoyHostel-From-Cafe', 'J-Integrity-Turn'),
    ('J-Bakery-Entrance', 'J-Integrity-From-Bakery'),
    ('J-Integrity-From-Bakery', 'J-Integrity-Turn'),
    ('J-Integrity-Turn', 'J-Integrity-From-BoyHostel'),
    ('J-Integrity-Turn', 'Integrity Entrance'),
    ('J-Integrity-From-BoyHostel', 'Joseph Entrance'),
    ('J-Integrity-From-BoyHostel', 'Elisha Entrance'),
    ('Elisha Entrance', 'Levi Entrance'),
    ('J-NewCafe-Back-Entrance', 'J-BoyHostel-From-Cafe'),
    ('J-NewCafe-Paved', 'J-BoyHostel-From-Cafe'),

    # === STAFF ===
    ('Staff Entrance', 'J-Integrity-From-BoyHostel'),
]


class Command(BaseCommand):
    help = 'Seed Caleb University campus with corrected real-world coordinates'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing data...')
        Edge.objects.all().delete()
        Waypoint.objects.all().delete()
        Building.objects.all().delete()

        # --- Buildings ---
        self.stdout.write('Creating buildings...')
        building_map = {}
        for data in BUILDINGS:
            b = Building.objects.create(**data)
            building_map[b.short_name] = b
            self.stdout.write(f'  ✓ {b.name}')

        # --- Building entrance waypoints ---
        self.stdout.write('Creating building entrance waypoints...')
        wp_map = {}
        for b in building_map.values():
            wp = Waypoint.objects.create(
                name=f'{b.short_name} Entrance',
                waypoint_type='entrance',
                latitude=b.latitude,
                longitude=b.longitude,
                building=b,
                is_active=True,
            )
            wp_map[wp.name] = wp

        # --- Junction waypoints ---
        self.stdout.write('Creating junction waypoints...')
        for (name, lat, lng) in WAYPOINTS:
            wp = Waypoint.objects.create(
                name=name,
                waypoint_type='junction',
                latitude=lat,
                longitude=lng,
                building=None,
                is_active=True,
            )
            wp_map[name] = wp
            self.stdout.write(f'  ✓ {name}')

        # --- Edges ---
        self.stdout.write('Creating path edges...')
        edge_count = 0
        skipped = []
        for (from_name, to_name) in MANUAL_EDGES:
            wp1 = wp_map.get(from_name)
            wp2 = wp_map.get(to_name)
            if not wp1 or not wp2:
                skipped.append(f'{from_name} → {to_name}')
                continue
            dist = haversine(wp1.latitude, wp1.longitude, wp2.latitude, wp2.longitude)
            if not Edge.objects.filter(from_waypoint=wp1, to_waypoint=wp2).exists() and \
               not Edge.objects.filter(from_waypoint=wp2, to_waypoint=wp1).exists():
                Edge.objects.create(
                    from_waypoint=wp1,
                    to_waypoint=wp2,
                    distance=round(dist, 2),
                    surface='footpath',
                    is_accessible=True,
                    is_active=True,
                )
                edge_count += 1

        if skipped:
            self.stdout.write(self.style.WARNING(
                f'\n  Skipped {len(skipped)} edges (waypoint name mismatch):'
            ))
            for s in skipped:
                self.stdout.write(f'    - {s}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {len(BUILDINGS)} buildings, '
            f'{len(WAYPOINTS)} junctions, {edge_count} edges created.'
        ))