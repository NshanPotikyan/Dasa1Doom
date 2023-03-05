hidden_assertions = {
    0: """""",
    1: ["""assert verbose(123) == 'հարյուր քսաներեք'
assert verbose(267) == 'երկու հարյուր վաթսունյոթ'
assert verbose(89) == 'ութսունինը'
assert verbose(11) == 'տասնմեկ'
assert verbose(10) == 'տասը'
assert verbose(5) == 'հինգ'
assert verbose(999) == 'ինը հարյուր իննսունինը' 
assert verbose(18) == 'տասնութ' 
assert verbose(100) == 'հարյուր' 
assert verbose(200) == 'երկու հարյուր' 
assert verbose(20) == 'քսան' 
assert verbose(78) == 'յոթանասունութ'""", 'verbose'],
    2: ["""assert calc('hello world! 123') == (10, 3)
assert calc('1994') == (0, 4)
assert calc('hello world!') == (10, 0)
assert calc('@#^$*&!') == (0, 0)
assert calc('aaaaaaaaa') == (9, 0) 
assert calc('11111') == (0, 5) 
assert calc('o1') == (1, 1) 
assert calc('') == (0, 0)""", 'calc'],
    3: ["""assert email_to_username('nshan@gmail.com') == 'nshan'
assert email_to_username('aramhayrapetyan@google.com') == 'aramhayrapetyan'
assert email_to_username('hayrapetyan@yahoo.com') == 'hayrapetyan'
assert email_to_username('something@fast.foundation') == 'something' 
assert email_to_username('aaaa@aaaa') == 'aaaa' 
assert email_to_username('s@.com') == 's'""", 'email_to_username'],
    4: ["""assert merge([1, 2, 5], [2, 3, 4]) == [1, 2, 2, 3, 4, 5]
assert merge([11, 25, 105],[2, 4, 38]) == [2, 4, 11, 25, 38, 105]
assert merge([1, 100, 101], [99, 100, 101]) == [1, 99, 100, 100, 101, 101] 
assert merge([-5, 0, 2], [-98, 5, 15]) == [-98, -5, 0, 2, 5, 15]""", 'merge'],
    5: ["""assert root(25, 2) == 5.0
assert root(16) == 4.0
assert root(81, 4) == 3.0
assert round(root(125, 3)) == 5 
assert round(root(66, 6)) == 2 
assert round(root(101, 2), 2) == 10.05""", 'root']
}
