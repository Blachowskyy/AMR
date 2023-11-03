#!/usr/bin/env python3

# number = 10.0
# number = str(number).replace('.', '')
# empty_list = []
# impulses = ''
# for i in number:
#     empty_list += i
#     # print(empty_list)
#     if len(empty_list) < 6:
#         impulses += i
#         print(type(impulses), impulses)

# impulses = int(impulses)
# print(type(impulses), impulses)

# def validation_angle_impulses(self):
#     impulses = round(self.angle_impulses, 2)
#     impulses = str(impulses * 100).replace('.', '')
#     # impulses = str(self.angle_impulses).replace('.', '')
#     empty_list = []
#     impulses1 = ''
#     for i in impulses:
#         empty_list += i
#         if len(empty_list) < 5:

#             impulses1 += i       
#     print(impulses1)      
#     self.angle_impulses = int(impulses1)    
angle_impulses = 20.10
impulses = round(angle_impulses, 1)
print(impulses)
impulses = str(impulses).replace('.', '')
# print(impulses)
# impulses = str(self.angle_impulses).replace('.', '')
empty_list = []
impulses1 = ''
for i in impulses:
    empty_list += i
    if len(empty_list) < 5:
        impulses1 += i       
print(impulses1)      
angle_impulses = int(impulses1 * 100) 