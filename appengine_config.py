import cProfile
import cStringIO
import logging
import pstats

if False:
    def webapp_add_wsgi_middleware(app):
        def profiling_wrapper(environ, start_response):
            profile = cProfile.Profile()
            response = profile.runcall(app, environ, start_response)
            stream = cStringIO.StringIO()
            stats = pstats.Stats(profile, stream=stream)
            stats.sort_stats('cumulative').print_stats()
            logging.info('Profile data:\n%s', stream.getvalue())
            return response

        return profiling_wrapper
