import json
from global_methods import *
import re


class Appointment:
    def __init__(self, date_time: datetime.datetime, name: str, people_involved: list, 
                 description: str = '', location: str = '', status: str = 'Scheduled', duration = 1):
        self.date_time = date_time
        self.name = name
        self.people_involved = people_involved
        self.description = description
        self.location = location
        self.status = status
        # maybe change this to a
        try:
            self.duration = int(duration)
        except:
            self.duration = 1

        #print(str(self))

    def get_duration(self):
        return datetime.timedelta(hours=self.duration)

    def to_dict(self):
        """Convert the appointment object to a dictionary for easy serialization."""
        return {
            'date_time': self.date_time.strftime('%Y-%m-%d %H:%M'),
            'name': self.name,
            'people_involved': self.people_involved,
            'description': self.description,
            'location': self.location,
            'status': self.status,
            'duration': self.duration
        }
    
    def from_dict(cls, data):
        """Create an Appointment object from a dictionary."""
        date_time = datetime.datetime.strptime(data['date_time'], '%Y-%m-%d %H:%M')
        
        return cls(
            date_time=date_time,
            name=data['name'].strip("\n"),
            people_involved=data['people_involved'],
            description=data['description'].strip("\n"),
            location=data['location'].strip("\n"),
            status=data['status'].strip("\n"),
            duration=int(data['duration']))
    
    

    '''def __repr__(self) -> str:
        return self.name'''
    
    def update_status(self, new_status: str):
        """Update the status of the appointment."""
        self.status = new_status

    def reschedule(self, new_date_time: datetime.datetime):
        """Reschedule the appointment to a new date and time."""
        self.date_time = new_date_time
    
    def add_person(self, scratch):
        """Add a person to the appointment."""
        if scratch.name not in self.people_involved:
            self.people_involved.append(scratch.name)

    def add_people(self, new_people):
        """Add new people to the appointment without duplication."""
        for person in new_people:
            if person not in self.people_involved:
                self.people_involved.append(person)
    
    def remove_person(self, person_name: str):
        """Remove a person from the appointment."""
        for p in self.people_involved:
            if p.name == person_name:
                self.people_involved.remove(p)

    def __str__(self):
        """Return a string representation of the appointment."""
        appointment_info = f"""
        Appointment Name: {self.name}
        Date & Time: {self.date_time.strftime('%Y-%m-%d %H:%M')}
        People Involved: {self.people_involved}
        Description: {self.description}
        Location: {self.location}
        Status: {self.status}
        Duration: {self.get_duration()}
        """
        return appointment_info

class Calendar:
    def __init__(self, filename=None, new=False):
        """Initialize the Calendar with an empty list of appointments or load from a JSON file."""
        self.appointments = []
        
        if filename and (not new) and check_if_file_exists(filename):
            self.load_from_json(filename)

    

    def create_appointment(self, name, location, date_time, people, description, duration):
        #print("CREATE")
        
                #pass
        #print(str_date_time)
        str_date_time = strip_time(date_time)

        if str_date_time is not None:
            self.match_appointment(name, location, description, str_date_time, people, duration)


    def load_from_json(self, filename: str):
        """Load appointments from a JSON file."""
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
            self.appointments = [Appointment.from_dict(Appointment, item) for item in data]
        #print(f"Appointments loaded from {filename}")

    

    def save(self, filename: str, curr_time):
        """Save the current and future appointments to a JSON file."""
        now = curr_time - datetime.timedelta(days=1)
        upcoming_appointments = [
            appointment.to_dict() for appointment in self.appointments
            if appointment.date_time >= now
        ]
        
        with open(filename, 'w') as json_file:
            json.dump(upcoming_appointments, json_file, indent=4)
        #print(f"Appointments saved to {filename}")

    def __repr__(self) -> str:
        return str([ str(ap) for ap in self.appointments])

    def add_appointment(self, appointment: Appointment):
        """Add an appointment to the calendar."""
        self.appointments.append(appointment)

    def keyword_matching(self, text):
        """Extract keywords from text by removing common stop words."""
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'so', 'is', 'are', 'was', 'were', 'am', 'in', 'on', 'at', 'of', 'for', 'with', 'by', 'to', 'from', 'that', 'this', 'it', 'he', 'she', 'they', 'we'}
        words = re.findall(r'\b\w+\b', text.lower())
        return set(word for word in words if word not in stop_words)
    
    def match_appointment(self, name, location, description, date_time, people_involved, duration):
        """Match a new appointment based on keywords in the name, location, and description."""
        #print("match")
        new_keywords = (
            self.keyword_matching(name) |
            self.keyword_matching(location) |
            self.keyword_matching(description)
        )

        for appointment in self.appointments:
            existing_keywords = (
                self.keyword_matching(appointment.name) |
                self.keyword_matching(appointment.location) |
                self.keyword_matching(appointment.description)
            )

            # Check if the keyword sets overlap significantly (e.g., more than half match)
            if len(new_keywords & existing_keywords) >= len(new_keywords) // 2:
                # Add new people to the existing appointment
                appointment.add_people(people_involved)
                #print(f"Matched with existing appointment: {appointment.name} on {appointment.date_time}")
                return 
        
        # If no match is found, add it as a new appointment
        new_appointment = Appointment(
                    date_time=date_time,
                    name=name,
                    people_involved=people_involved,
                    description=description,
                    location=location,
                    duration=duration
                )
        self.add_appointment(new_appointment)
        #print(f"New appointment added: {new_appointment.name} on {new_appointment.date_time}")

    def get_future_appointments(self,scratch, time_frame: datetime.timedelta):
        """Get appointments within the specified future time frame from now."""
        now = scratch.curr_time
        #now = persona.curr_time

        #print(now)

        #for appointment in self.appointments:
            #print(appointment)

        future_appointments = [
            appointment for appointment in self.appointments
            if now <= appointment.date_time <= now + time_frame and scratch.name in appointment.people_involved
        ]
        return future_appointments
    
    def get_current_appointments(self,scratch):
        """Get appointments within the specified future time frame from now."""
        now = scratch.curr_time
        #now = persona.curr_time

        '''print(now)

        for appointment in self.appointments:
            print(appointment.name + " = " + str(appointment.date_time))'''

        _appointments = [
            appointment for appointment in self.appointments
            if  appointment.date_time <= now <= appointment.date_time + appointment.get_duration()
 and scratch.name in appointment.people_involved
        ]
        return _appointments
    
    def get_appointments_for_next_day(self, scratch):
        """Get appointments scheduled for the next 24 hours."""
        return self.get_future_appointments(scratch, datetime.timedelta(days=1))

    def get_appointments_for_next_hour(self, scratch):
        """Get appointments scheduled for the next 1 hour."""
        return self.get_future_appointments(scratch, datetime.timedelta(hours=1))
    
    def get_appointments_for_next_month(self, scratch):
        """Get appointments scheduled for the next 1 hour."""
        return self.get_future_appointments(scratch, datetime.timedelta(days=30))
    
    def get_appointments_for_next_year(self, scratch):
        """Get appointments scheduled for the next 1 hour."""
        return self.get_future_appointments(scratch, datetime.timedelta(year=1))


    def display_appointments(self, appointments, scratch):
        """Helper method to display a list of appointments."""
        if not appointments:
            print("No appointments found.")
        else:
            print(f"Appointments for {scratch.name}")
            for appointment in appointments:
                print(appointment)

    def update_status(self, now):
        for i in range(len(self.appointments)):
            ap = self.appointments[i]
            if ap.date_time <= now <= ap.date_time+ap.get_duration():
                self.appointments[i].status = "Ongoing"
            elif now > ap.date_time + ap.get_duration():
                self.appointments[i].status = "Ending"

    def get_appointments(self, scratch):
        now = scratch.curr_time

        
        self.update_status(now)

        _str = ""
        _appointments=None
        futute_appointments = None
        current = self.get_current_appointments(scratch)
        #print(self)

        if len(current)==0:
            current = None
            _appointments = self.get_appointments_for_next_hour(scratch)

            if len(_appointments)==0:
                _appointments = None
                futute_appointments = self.get_appointments_for_next_day(scratch)
                if len(futute_appointments) == 0:
                    futute_appointments = None

        if current is not None or _appointments is not None or futute_appointments is not None:
            if current is not None:
                str_apps = ""
                for app in current:
                    str_apps += str(app) + "\n"
                _str = f"Here is a list of {scratch.name}'s current appointments that are happening RIGHT NOW and that they ARE NOW PARTICIPATING IN: {str_apps}"
            
            elif _appointments is not None:
                str_apps = ""
                for app in _appointments:
                    str_apps += str(app) + "\n"
                _str = f"Here is a list of {scratch.name}'s current appointments that are happening IN THIS NEXT HOUR and that they MUST attend: {str_apps}"
            elif futute_appointments is not None:
                str_apps = ""
                for app in futute_appointments:
                    str_apps += str(app) + "\n"
                _str = f"Here is a list of {scratch.name}'s appointments that are happening TODAY and that they MUST attend: {str_apps}"
        return _str
    

# Example Usage:

class p:
    def __init__(self, name):
        self.name = name
        self.curr_time = datetime.datetime.now()

    def __repr__(self) -> str:
        return self.name


if __name__ == "__main__":
    # Create the calendar
    calendar = Calendar()

    personas = [persona for persona in [p("Alice"), p("Bob"), p("Charlie") ]]
    print(personas)

    # Create some appointments
    appointment1 = Appointment(
        date_time=datetime.datetime.now() + datetime.timedelta(hours=0.5),
        name="Team Meeting",
        people_involved=personas,
        description="Discuss project progress",
        location="Conference Room A"
    )

    appointment2 = Appointment(
        date_time=datetime.datetime.now() + datetime.timedelta(days=0.5),
        name="Doctor's Appointment",
        people_involved=[personas[0]],
        description="Routine check-up",
        location="Clinic"
    )

    appointment3 = Appointment(
        date_time=datetime.datetime.now() + datetime.timedelta(hours=0.5),  # Assuming this is within the next hour
        name="Client Call",
        people_involved=[personas[1:2]],
        description="Discuss project requirements",
        location="Zoom"
    )

    # Add appointments to the calendar
    calendar.add_appointment(appointment1)
    calendar.add_appointment(appointment2)
    calendar.add_appointment(appointment3)

    #print(calendar)

    # Display appointments for the next day
    print("Appointments for the next day:")
    calendar.display_appointments(calendar.get_appointments_for_next_day(personas[0]), personas[0])

    # Display appointments for the next hour
    print("\nAppointments for the next hour:")
    calendar.display_appointments(calendar.get_appointments_for_next_hour(personas[1]), personas[1])
