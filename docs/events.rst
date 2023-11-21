.. _events:

Listening for changes
=====================


WAPI supports listening for changes to curves.  An event listener is set up, and behaves
like an infinite iterator, returning change events as they happen.

To create an event listener, find a list of curves (or a list of curve ids) and use that
as input to the :meth:`volue_insight_timeseries.session.Session.events` function.  There are two optional arguments:
``start_time`` (if you had a listener and you want to restart it without getting old events), and
``timeout`` if you do not want the iterator to wait for ever.

When a curve is updated, the iterator returns a :class:`~volue_insight_timeseries.events.CurveEvent`
object (:class:`volue_insight_timeseries.events.CurveEvent`).  If ``timeout`` is specified and expires,
a :class:`~volue_insight_timeseries.events.EventTimeout` object (:class:`volue_insight_timeseries.events.EventTimeout`) is returned::

    >>> curves = session.search(category='WND', area=['EE', 'LT'], frequency='H')
    >>> events = session.events(curves, timeout=5)
    >>> for e in events:
            print(e)
    ...

.. automethod:: volue_insight_timeseries.session.Session.events
    :noindex:
