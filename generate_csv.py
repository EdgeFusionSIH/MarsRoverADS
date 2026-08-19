import csv
import random

def generate():
    print("Generating extended Mars Rover CSV...")
    with open('node2/dataset/mars_rover_sensor_data.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['TIMESTAMP', 'Image numbers', 'Wheel slip (%)', 'Torque (%)', 'Solar (%)'])

        # Total 150 seconds, 0.25s intervals -> 600 rows
        for i in range(1, 601):
            ts = i * 0.25
            img_num = i
            
            if ts <= 50.0:
                # Normal (0-50s)
                slip = random.uniform(2.0, 6.0)
                torque = random.uniform(8.0, 12.0)
                solar = random.uniform(95.0, 100.0)
            elif ts <= 100.0:
                # Dust Storm (50-100s)
                slip = random.uniform(5.0, 15.0)
                torque = random.uniform(10.0, 18.0)
                # Solar drops from 95% down to 25% steadily
                progress = (ts - 50.0) / 50.0
                solar = 95.0 - (70.0 * progress) + random.uniform(-2, 2)
                # Clamp solar
                solar = max(10.0, min(100.0, solar))
            else:
                # Sand Trap (100-150s)
                slip = random.uniform(40.0, 95.0)
                torque = random.uniform(40.0, 90.0)
                solar = random.uniform(20.0, 30.0)
            
            writer.writerow([f"{ts:.2f}", img_num, f"{slip:.2f}", f"{torque:.2f}", f"{solar:.2f}"])
            
    print("Done! Generated 600 rows (150 seconds at 0.25s intervals).")

if __name__ == '__main__':
    generate()
