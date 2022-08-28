from datetime import datetime, date
from flask import Flask, abort
import sys
from flask_restful import Api, Resource, reqparse
from flask_restful import inputs, marshal_with, fields
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event_database.db'


# Define a database structure
class Event(db.Model):
    __tablename__ = 'table_name'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)


# Create a database
db.create_all()

parser = reqparse.RequestParser()
parser_2 = reqparse.RequestParser()
parser.add_argument('event', type=str, help="The event name is required!", required=True)
parser.add_argument('date', type=inputs.date, help="The event date with the correct format is required! "
                                                   "The correct format is YYYY-MM-DD!", required=True)
parser_2.add_argument('start_time', type=inputs.date)
parser_2.add_argument('end_time', type=inputs.date)


# Create a class to marshall data
class TodoEvent(object):
    def __init__(self, id, event, date):
        self.id = id
        self.event = event
        self.date = date


# Create a template to marshall data
resource_fields = {
    'id': fields.Integer,
    'event': fields.String,
    'date': fields.String
}


class EventResource(Resource):

    @marshal_with(resource_fields)
    def get(self, **kwargs):
        query = Event.query.all()
        current_time = datetime.now().strftime('%Y-%m-%d')

        today_event = [TodoEvent(id=item.id, event=item.event, date=item.date) for item in query
                       if current_time == str(item.date)]

        if today_event:
            return today_event
        else:
            return {"data": "There are no events for today!"}


class PostEventResource(Resource):

    @marshal_with(resource_fields)
    def get(self, **kwargs):
        args = parser_2.parse_args()
        start_time = args['start_time']
        end_time = args['end_time']

        # Retrieve data from a database
        query = Event.query.all()

        if start_time and end_time:
            # Take time from arguments and convert from datetime to date in order to compare with the database value
            start_time = args['start_time'].date()
            end_time = args['end_time'].date()

            output_list = [TodoEvent(id=item.id, event=item.event, date=item.date) for item in query
                           if end_time >= item.date >= start_time]
            if output_list:
                return output_list
        else:
            output_list = [TodoEvent(id=item.id, event=item.event, date=item.date) for item in query]
            return output_list

    def post(self):
        args = parser.parse_args()
        date = str(args['date']).split()[0]
        new_event = Event(event=args['event'], date=args['date'])

        # Save to the database
        db.session.add(new_event)
        db.session.commit()
        return {"message": "The event has been added!", "event": args['event'], "date": date}


class EventByID(Resource):

    @marshal_with(resource_fields)
    def get(self, event_id, **kwargs):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        return event

    def delete(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        print('delete')

        if event is None:
            abort(404, "The event doesn't exist!")
        else:
            db.session.delete(event)
            db.session.commit()
            return {"message": "The event has been deleted!"}


api.add_resource(EventByID, '/event/<int:event_id>')
api.add_resource(EventResource, '/event/today')
api.add_resource(PostEventResource, '/event')


# do not change the way you run the program
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
