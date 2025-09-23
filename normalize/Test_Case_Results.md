Test Case 1:                                                                                                                          
    Text: "Hi Fora, I'm Alex Smith (917-555-1234) in 10003. My client flies to Rome next week and just lost her passport—help!"
    JSON Response:
    {
      "message_id": "test-case-1",
      "category": "high_risk",
      "contact": {
        "first_name": "Alex",
        "last_name": "Smith",
        "email": null,
        "phone": "9175551234",
        "zip": "10003"
      },
      "entities": [
        {
          "type": "city",
          "value": "rome"
        }
      ],
      "enrichment": {
        "local_emergency_numbers": [
          "112",
    "113"
        ],
        "city_typo": null,
        "country_typo": null,
        "phone_number_typo": null,
        "zip_code_typo": null
      }
    }

    Test Case 2:
    Text: "Hi Fora, I'm Alex. My client is flying next week and just lost her passport—help!"
    JSON Response:
    {
      "message_id": "test-case-2",
      "category": "high_risk",
      "contact": {
        "first_name": "Alex",
        "last_name": null,
        "email": null,
        "phone": null,
        "zip": null
      },
      "entities": null,
      "enrichment": null
    }

    Test Case 3:
    Text: "my wallet was stolen in Paris last night"
    JSON Response:
    {
      "message_id": "test-case-3",
      "category": "high_risk",
      "contact": null,
      "entities": [
        {
          "type": "city",
          "value": "paris"
        }
      ],
      "enrichment": {
        "local_emergency_numbers": [
          "112",
    "17"
        ],
        "city_typo": null,
        "country_typo": null,
        "phone_number_typo": null,
        "zip_code_typo": null
      }
    }

    Test Case 4:
    Text: "flight in 3 h, need assistance"
    JSON Response:
    {
      "message_id": "test-case-4",
      "category": "urgent",
      "contact": null,
      "entities": null,
      "enrichment": null
    }

    Test Case 5:
    Text: "planning Rome in October with a stay at Chapter Roma and maybe NYC"
    JSON Response:
    {
      "message_id": "test-case-5",
      "category": "base",
      "contact": null,
      "entities": [
        {
          "type": "city",
          "value": "rome"
        },
        {
          "type": "city",
          "value": "nyc"
        },
        {
          "type": "hotel",
          "value": "chapter roma"
        }
      ],
      "enrichment": {
        "local_emergency_numbers": [
          "112",
          "113",
    "911"
        ],
        "city_typo": null,
        "country_typo": null,
        "phone_number_typo": null,
        "zip_code_typo": null
      }
    }

    Test Case 6:
    Text: "I am going to eat at Randy's Pub in the 95463 zip code, and I need to get to the airport in 2 hours. Can you book me a flight?"
    JSON Response:
    {
      "message_id": "test-case-6",
      "category": "urgent",
      "contact": {
        "first_name": null,
        "last_name": null,
        "email": null,
        "phone": null,
        "zip": "95463"
      },
      "entities": [
        {
          "type": "restaurant",
          "value": "randy's pub"
        }
      ],
      "enrichment": null
    }

    Test Case 7:
    Text: "I am currently staying at Ritz Carlton in Germany. But I want to book another hotel ASAP. Can you help?"
    JSON Response:
    {
      "message_id": "test-case-7",
      "category": "urgent",
      "contact": null,
      "entities": [
        {
          "type": "country",
          "value": "germany"
        },
        {
          "type": "hotel",
          "value": "ritz carlton"
        }
      ],
      "enrichment": {
        "local_emergency_numbers": [
          "112",
    "110"
        ],
        "city_typo": null,
        "country_typo": null,
        "phone_number_typo": null,
        "zip_code_typo": null
      }
    }

    Test Case 8:
    Text: "I am Dr. Singh. Also known as Eric. I need some immediate help. Call me 661248083"
    JSON Response:
    {
      "message_id": "test-case-8",
      "category": "urgent",
      "contact": {
        "first_name": "Eric",
        "last_name": "Singh",
        "email": null,
        "phone": null,
        "zip": null
      },
      "entities": null,
      "enrichment": {
        "local_emergency_numbers": null,
        "city_typo": null,
        "country_typo": null,
        "phone_number_typo": "661248083",
        "zip_code_typo": null
      }
    }

    Test Case 9:
    Text: "I'm in the 91355 zie code in Brlin, and I need to go to Mexico ASAP. Can you book me a flight?"
    JSON Response:
    {
      "message_id": "test-case-9",
      "category": "urgent",
      "contact": {
        "first_name": null,
        "last_name": null,
        "email": null,
        "phone": null,
        "zip": "91355"
      },
      "entities": [
        {
          "type": "city",
          "value": "brlin"
        },
        {
          "type": "country",
          "value": "mexico"
        }
      ],
      "enrichment": {
        "local_emergency_numbers": [
    "060"
        ],
        "city_typo": "brlin -> berlin",
        "country_typo": null,
        "phone_number_typo": null,
        "zip_code_typo": "91355 -> 5 digits expected"
      }
    }

    Test Case 10:
    Text: "I'm in Ls Anglees, need to travel to Toronto. I am feeling very scared and want to leave immediately. Call me 818900600"
    JSON Response:
    {
      "message_id": "test-case-10",
      "category": "high_risk",
      "contact": null,
      "entities": [
        {
          "type": "city",
          "value": "los angeles"
        },
        {
          "type": "city",
          "value": "toronto"
        }
      ],
      "enrichment": {
        "local_emergency_numbers": [
    "911"
        ],
        "city_typo": "ls anglees -> los angeles",
        "country_typo": null,
        "phone_number_typo": "818900600",
        "zip_code_typo": null
      }
    }
