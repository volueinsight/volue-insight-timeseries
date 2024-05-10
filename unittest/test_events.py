import volue_insight_timeseries as vit
import json

prefix = 'rtsp://test.host/api'


def test_events(session, ts_curve, inst_curve):
    s, m = session
    c1 = ts_curve[0]
    c2 = inst_curve[0]
    sse_data = []
    ids = [5, 7, 7, 7, 5, 5, 7]
    for n, id_ in enumerate(ids):
        d = {'id': id_, 'created': '2016-10-01T00:01:02.345+01:00', 'operation': 'modify',
             'range': {'begin': None, 'end': None}}
        sse_data.append('id: {}\nevent: curve_event\ndata: {}\n\n'.format(n, json.dumps(d)))
    m.register_uri('GET', prefix + '/events?id=5&id=7', text=''.join(sse_data))
    with vit.events.EventListener(s, [c1, c2]) as e:
        for n, id_ in enumerate(ids):
            event = e.get()
            assert isinstance(event, vit.events.CurveEvent)
            assert event.id == id_
            assert isinstance(event.curve, vit.curves.BaseCurve)
