Club_Mate [Pwn, 144 points, 33 solves]
===========

This challenge is a service written in C that allows you to buy and sell Club Mate drinks from a vending machine. The goal is to buy out all of the drinks while having effectively max money.


### Reverse Engineering

From reverse engineering the challenge binary with IDA Pro, there are a couple of bugs that I was able to find. I only ended up using one of them for my exploit though. The program creates an array of 15 ClubMate structures to keep track of inventory. Here is my reverse engineered definition of that object:

```c
struct ClubMate
{
  char description_top[20];    // ClubMate+0, 20 bytes
  char description_middle[20]; // ClubMate+20, 20 bytes
  char description_bottom[20]; // ClubMate+40, 20 bytes
  bool isAvailable;            // ClubMate+60, 1 byte
};
```

As the program runs, you are asked for the number of the ClubMate that you would like to buy/sell. It takes this number and uses it as an index into the array of ClubMate structs to get the selected one. If the selected ClubMate's isAvailable field is true, then it asks if you want to buy it. Otherwise, it asks if you want to return that ClubMate. It costs \$4 to buy a ClubMate, and when you return one, by default you are refunded \$3.

Here's what the win condition looks like in simplified pseudocode:

```c
ClubMate item_array[15];
int refund_amount;
uint8_t cur_money;

//...snip...

if(!vending_machine_has_stock(item_array) && refund_amount + 250 < cur_money )
      print_flag();
```

Therefore, assuming that `refund_amount` is still set to its default value of 3, then the goal is to have either 254 or 255 as your `cur_money` value at the time when you buy the last ClubMate.


### Vulnerabilities

1. The number you enter when selecting a ClubMate is used as an index into `item_array` without any bounds checks. Therefore, even though the valid indices are only 0-14, you can enter items past the end of the array like 15-99 or negative values like -1 through -9. You can only enter two characters, which is what determines these limits.
2. You are allowed to buy a ClubMate even if you don't have the $4 needed. This will cause your money value to integer overflow back around to UINT8_MAX (255).


### The Exploit

While testing this, the obvious approach is to just use the money overflow (bug #2) to have your money value be either \$2 or \$3 when you buy the last ClubMate so that during the win check your money will be either \$254 or \$255, thereby passing the win check and printing the flag. However, this approach requires buying and selling the same item about 200 times, which combined with network lag means an exploit script likely won't be able to complete before the timeout happens.

This caused me and my teammate to look into using bug #1 with index -1, which corrupts the `refund_amount` variable, setting it to 0xd (13) instead of 3. The problem is that this makes the challenge impossible to win, as 250 + 13 is 263, which is larger than the maximum possible value of `cur_money` (255). I couldn't discover any way to get the value of `refund_amount` to have a different value besides 3 and 13, so I stopped looking at this bug.

I eventually realized that the problem with my initial approach was the compounding network lag from sending an input, waiting for a response, sending the next input, waiting for that response, etc. So to overcome this network lag, I came up with this as my solution. I ran the money overflow solution (bug #2) against the program locally, and I wrote every input my script sent to the program to a file [`payload.txt`](payload.txt). Then, to send this payload to the remote challenge server without the network lag from waiting for a response after each input, I ran this command:

```bash
(cat payload.txt; cat) | nc 13.48.178.241 50000
```

Because the exploit doesn't require any information that the server sends back, the same input can be reused every time, which is why sending it all in one shot like this works. This command caused the challenge to enter the correct win state and send me the flag.