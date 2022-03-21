---
title: "Why Everyone Should Use AWS Control Tower"
date: 2022-03-21T09:00:00-06:00
draft: true
---

My life for the past 10 months has involved a lot of [AWS Control Tower](https://aws.amazon.com/controltower/). I helped build the [Control Tower Catalyst at Caylent](https://aws.amazon.com/marketplace/pp/prodview-lvbpoeljjvqmo) and have been involved in delivering, selling, or troubleshooting it well over two dozen times at this point. Prior to joining Caylent, I knew at a high level what Control Tower was and why enterprises might use it, but I had very little hands on with it and didn't care for much. It felt like another half baked GA release. But I am here to tell you now that you (<em>points finger through the screen</em>) that my opinions on it have changed, and why everyone (even you, non-enterprise person) should also use Control Tower if you find yourself being a builder/tinkerer inside of AWS. 

# What is AWS Control Tower?

Let's start with the basics.

[AWS Control Tower](https://aws.amazon.com/controltower/) is a service provided by AWS that is meant to be, wait for it, your Control Tower. It is meant to be a one-stop-shop for creating, managing, and organizing AWS accounts. The goal with AWS Control Tower is to give you the ability to organize your accounts in logical buckets (Organization Units or OU) and then apply broad controls to those buckets for security, governance, or compliance.

After Control Tower went GA, AWS introduced additional automations which make it even more powerful. With the addition of [Customization for Control Tower](https://aws.amazon.com/solutions/implementations/customizations-for-aws-control-tower/) or [Account Factory for Terraform](https://aws.amazon.com/blogs/aws/new-aws-control-tower-account-factory-for-terraform/) (I did a [webinar](https://www.youtube.com/watch?v=cRRDg2tlC6U) on AFT if you are interested), you can control even more infrastructure as code deployments to these accounts. These tools are more or less the same, but they allow you to essentially define a cookie-cutter of what your accounts should look like, and every time you build one, it will come out as a ready-to-use account. Gone are the days of spinning up a shell of an account and requiring someone to manually deploy into it - this is all automated now.


# But why should I (non-enterprise person) care

I feel like selling AWS Control Tower to the enterprise is easy, you know, unless they hate automation and love manual, error-prone work. But why should you, the person reading this, who is most likely not the CTO of a company, use AWS Control Tower? Well, let me tell you why I use it.

## Disposable Accounts

This is a concept that I think a lot of people have yet to embrace, but over the last several years AWS accounts have become less "sacred ground" that you don't want to mess up and have transitioned into more disposable assets. If you are going to test out a new service, or build a new app, or give Joe Shmo a virtual playground - spin up a new account. Use that account for as long as you need, and then discard it. Don't even worry about deleting the resource inside of it, just delete it and forget about it.

AWS Control Tower with its centralized billing makes it so simple to create new accounts. Provide an email, give it a name, wait 30 minutes, and magic.

Personally, I spin up an account for any random thing that I work on. This blog, a new account. My resume website, new account. Some curling automation that I did, new account. My brewery tracker app (which is a conversation for another time), new account. I think I have seven or eight accounts in my control tower that are just for personal use and personal project. If I ever needed to give someone access to tinker with one of my projects, it is secluded from everything else. If I ever decide to shut down this blog, I just delete the account. It is a fantastic feature that often goes underutilized both for personal use, and for businesses.

Also, individuals often think that this account-level sprawl means cost. I am here to tell you that it does not. My bill last month for all of my accounts was under $20. Accounts are free, you only pay for the resources deployed into them. While Control Tower out of the box does deploy services into each account, these services are not expensive.

## Single Sign-On

If you end up building multiple accounts, then the out of the box easy to manage AWS SSO is a no-brainer. AWS SSO gives you the ability to log in to all of your accounts while managing a single identity. It also gives you programmatic access to all of your accounts so that you can interact with the CLI easily with temporary credentials and not have to worry about someone stealing them or hacking into your account.

![AWS SSO](/images/post02-AWS-SSO.png)

## Billing alarms

With disposable accounts, account sprawl can be a problem. I use Control Tower and the Control Tower automations mentioned above to deploy billing alarms to my accounts. This ensures that my bills stay where I expect them to, and if they are rising for any reason I get an email and can address them. It is a good way to not only keep my project under control but also to alert me about accounts that I haven't logged into in months should the bill rise for any reason.


# But I am a CTO of a very important enterprise company and I somehow stumbled onto your blog.

Great. Welcome. Let me cover a few more of the use cases that I think make this a no-brainer for people like you to adopt.


## Service Control Policies (SCPs)

Service control policies are arguably the biggest benefit that comes with AWS Control Tower. <em>This is where someone in the back of the room screams "SCPs are part of AWS Organizations, not Control Tower" and we then ask them to leave.</em> SCPs are overarching policies that you can apply to your accounts that can block various actions. Generally, it is recommended that you apply these at an OU level so that all new accounts put into that OU are automatically protected by this policy. I think SCPs are best explained by some examples.

Imagine a Sandbox OU where you allow developers to have their own accounts that they could use to deploy your application, test new services, or do general sandbox things. With any sandbox, you are concerned about cost. What if you could block large and expensive instance types so that no one accidentally deploys an m5.12xlarge and forgets to shut it down? What if you could deny expensive big data and ML services so that no one spins those up and drives up your bill? What if you can enforce a subset of images (AMIs) that you have pre-approved that contain your company-required anti-virus on them? All of these things are possible with SCPs and can be applied broadly across sets of accounts.

Now let's flip it around, maybe you don't have a sandbox but I am sure you have a production account (or multiple). Let's imagine what an SCP might look like on a production OU. You can deny all regions where your workload does not run. You could deny all services that aren't part of your production footprint. You can enforce that resources are only deployed via pipelines or IaC.

## Alarms

I am sure if you are an enterprise you have some expensive SIEM system, but what if I told you having consistent alarms across all accounts was even easier. With Control Tower and the automations you can build, it is very easy to build alarms in infrastructure as code and have them deployed across all accounts. You can alert on security events, you can alert on authorized users doing things they aren't supposed to, you can alert on an account exceeding a billing threshold. All of these things can be deployed broadly across all accounts.

## Networking

It is pretty common knowledge at this point that the default AWS VPC just doesn't cut it. Imagine if every time you spun up an account, you could deploy a best practices VPC into that account so that it is ready to use immediately. What if you could also establish interconnectivity to other VPCs? This is all possible using AWS Control Tower and these automations.

# Conclussion

Okay - I got a little carried away. But in the last 10 months, I have gone from not caring about AWS Control Tower into a Control Tower fanboy. Some might say it is because I get paid to be a fanboy, but it is more than that. Developing and deploying auotmations for Control Tower forced me to get deep into the weeds on the service and the automations that AWS has released to pair with it. They are extremely powerful and provide things that have been missing or been custom-built for a long time. Even for the the individual who just likes to tinker - being able to automate a few things into your accounts means you never have to worry about them again.

As always, would love to hear feedback/comments/questions/concerns. Are there things you want to be hear my opinion about? - blog@claytondavis.dev.



